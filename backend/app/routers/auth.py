from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

# passlib : pour chiffrer et vérifier les mots de passe
import bcrypt

# jose : pour créer et lire les tokens JWT
from jose import JWTError, jwt

from app import models, schemas
from app.database import get_db
from app.config import settings

# On crée un "routeur" — un groupe de routes liées à l'authentification
# prefix="/auth" : toutes les routes ici commenceront par /auth
router = APIRouter(prefix="/auth", tags=["Authentification"])

# CryptContext configure l'algorithme de chiffrement des mots de passe
# bcrypt est le standard de l'industrie pour ça
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") (utile quand j'utilisais encore passlib)

# Algorithme pour les tokens JWT
ALGORITHM = "HS256"

# --- Fonctions utilitaires ---

def hash_password(password: str) -> str:
    """Transforme un mot de passe en empreinte illisible"""
    # encode() convertit la string en bytes (bcrypt travaille en bytes)
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie que le mot de passe correspond à l'empreinte stockée"""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(data: dict) -> str:
    """Crée un token JWT qui expire après X minutes"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})   # "exp" = date d'expiration (standard JWT)
    # jwt.encode crée le token signé avec notre clé secrète
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)

# --- Routes ---

@router.post("/register", response_model=schemas.UserResponse, status_code=201)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Inscription d'un nouvel utilisateur.
    @router.post : cette fonction répond aux requêtes POST sur /auth/register
    response_model : FastAPI formate automatiquement la réponse selon UserResponse
    Depends(get_db) : FastAPI injecte automatiquement une session DB
    """

    # Vérifie si l'email est déjà utilisé
    existing = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing:
        # HTTPException : renvoie une erreur HTTP avec un code et un message
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà utilisé"
        )

    # Vérifie si le nom d'utilisateur est déjà pris
    existing_username = db.query(models.User).filter(
        models.User.username == user_data.username
    ).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce nom d'utilisateur est déjà pris"
        )

    # Crée le nouvel utilisateur avec le mot de passe chiffré
    new_user = models.User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hash_password(user_data.password)
        # On ne stocke PAS user_data.password directement !
    )

    db.add(new_user)      # Prépare l'insertion
    db.commit()           # Valide et envoie à la base de données
    db.refresh(new_user)  # Recharge l'objet pour récupérer l'id généré par la DB

    return new_user


@router.post("/login", response_model=schemas.Token)
def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    """Connexion — renvoie un token JWT si les identifiants sont corrects"""

    # Cherche l'utilisateur par email
    user = db.query(models.User).filter(models.User.email == credentials.email).first()

    # On vérifie les deux conditions dans le même bloc pour ne pas révéler
    # si c'est l'email ou le mot de passe qui est faux (sécurité)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte a été suspendu"
        )

    # Crée le token avec l'email comme identifiant
    token = create_access_token(data={"sub": user.email})

    return {"access_token": token, "token_type": "bearer"}