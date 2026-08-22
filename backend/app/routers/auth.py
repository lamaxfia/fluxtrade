from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from app.email_service import (
    generate_verification_code,
    send_verification_email,
    send_welcome_email
)
import logging
logger = logging.getLogger(__name__)

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

# On stocke temporairement les inscriptions en attente
# clé = email, valeur = {username, hashed_password, code, expires}
pending_registrations = {}

@router.post("/register", status_code=201)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Étape 1 : Envoie le code de vérification.
    Le compte N'EST PAS encore créé — il le sera après vérification.
    """
    # Vérifie si email déjà utilisé par un compte VÉRIFIÉ
    existing = db.query(models.User).filter(
        models.User.email == user_data.email,
        models.User.is_verified == True
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")

    # Vérifie si username déjà pris
    existing_username = db.query(models.User).filter(
        models.User.username == user_data.username,
        models.User.is_verified == True
    ).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="Ce nom d'utilisateur est déjà pris")

    # Supprime les comptes non vérifiés existants avec cet email
    db.query(models.User).filter(
        models.User.email == user_data.email,
        models.User.is_verified == False
    ).delete()
    db.commit()

    # Génère et envoie le code
    code = generate_verification_code()
    expires = datetime.utcnow() + timedelta(minutes=15)

    # Crée le compte en attente (non vérifié)
    new_user = models.User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
        is_verified=False,
        verification_code=code,
        verification_expires=expires
    )
    db.add(new_user)
    db.commit()

    # Envoie l'email
    email_sent = send_verification_email(user_data.email, user_data.username, code)
    if not email_sent:
        logger.warning(f"Email non envoyé à {user_data.email} — vérification manuelle requise")

    return {"message": "Code envoyé", "email": user_data.email, "status": "pending_verification"}


@router.post("/login", response_model=schemas.Token)
def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Ce compte a été suspendu")

    # Bloque si email non vérifié
    if not user.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Email non vérifié — vérifie ta boîte mail"
        )

    token = create_access_token(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


class VerifyCodeRequest(BaseModel):
    email: str
    code: str

@router.post("/verify-email")
def verify_email(data: VerifyCodeRequest, db: Session = Depends(get_db)):
    """Vérifie le code envoyé par email"""
    user = db.query(models.User).filter(models.User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    if user.is_verified:
        return {"message": "Email déjà vérifié"}

    if not user.verification_code or user.verification_code != data.code:
        raise HTTPException(status_code=400, detail="Code invalide")

    if user.verification_expires and user.verification_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Code expiré — demande un nouveau code")

    # Active le compte
    user.is_verified = True
    user.verification_code = None
    user.verification_expires = None
    db.commit()

    # Email de bienvenue
    send_welcome_email(user.email, user.username)

    return {"message": "Email vérifié avec succès"}


@router.post("/resend-verification")
def resend_verification(email: str, db: Session = Depends(get_db)):
    """Renvoie un nouveau code de vérification"""
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    if user.is_verified:
        return {"message": "Email déjà vérifié"}

    code = generate_verification_code()
    user.verification_code = code
    user.verification_expires = datetime.utcnow() + timedelta(minutes=15)
    db.commit()

    send_verification_email(user.email, user.username, code)
    return {"message": "Nouveau code envoyé"}