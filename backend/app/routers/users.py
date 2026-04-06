from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app import models, schemas
from app.database import get_db
from app.config import settings
from app.routers.auth import ALGORITHM

# Le routeur pour tout ce qui concerne le profil utilisateur
router = APIRouter(prefix="/users", tags=["Utilisateurs"])

# --- Fonction utilitaire : identifier l'utilisateur depuis son token ---

def get_current_user(
    token: str,           # le token JWT envoyé par le frontend
    db: Session = Depends(get_db)
):
    """
    Décode le token JWT et retourne l'utilisateur correspondant.
    Cette fonction sera réutilisée dans toutes les routes qui nécessitent
    d'être connecté — on l'injectera avec Depends()
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Décode le token avec notre clé secrète
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        email: str = payload.get("sub")  # "sub" = subject = l'email qu'on a mis dedans
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Cherche l'utilisateur en base de données
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user


# --- Routes ---

@router.get("/me", response_model=schemas.UserResponse)
def get_my_profile(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Retourne le profil de l'utilisateur actuellement connecté.
    Le frontend enverra son token pour s'identifier.
    """
    return get_current_user(token, db)


@router.put("/me/broker", response_model=schemas.UserResponse)
def update_broker_keys(
    broker_data: schemas.BrokerUpdate,
    token: str,
    db: Session = Depends(get_db)
):
    """
    Permet à l'utilisateur de sauvegarder ses clés API broker.
    Ces clés seront utilisées par l'agent de trading.
    """
    current_user = get_current_user(token, db)

    current_user.broker_api_key = broker_data.broker_api_key
    current_user.broker_api_secret = broker_data.broker_api_secret

    db.commit()
    db.refresh(current_user)
    return current_user