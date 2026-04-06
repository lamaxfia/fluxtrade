# Pydantic valide les données AVANT qu'elles touchent la base de données
# C'est le "videur" de la boîte de nuit — il vérifie les papiers à l'entrée
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# --- Schémas pour l'inscription ---

class UserCreate(BaseModel):
    """Données attendues quand quelqu'un s'inscrit"""
    email: EmailStr          # EmailStr vérifie que c'est un vrai format email
    username: str
    password: str

class UserLogin(BaseModel):
    """Données attendues pour se connecter"""
    email: EmailStr
    password: str

# --- Schéma de réponse (ce qu'on renvoie au frontend) ---

class UserResponse(BaseModel):
    """Ce qu'on renvoie après inscription ou connexion — SANS le mot de passe"""
    id: int
    email: str
    username: str
    is_active: bool
    is_admin: bool
    subscription_type: str
    created_at: datetime

    # orm_mode = True : permet à Pydantic de lire un objet SQLAlchemy
    # (par défaut Pydantic ne sait lire que des dictionnaires)
    class Config:
        from_attributes = True

# --- Schéma pour le token de connexion ---

class Token(BaseModel):
    """Ce qu'on renvoie après une connexion réussie"""
    access_token: str    # le token JWT
    token_type: str      # toujours "bearer"

class TokenData(BaseModel):
    """Ce qu'on extrait du token pour identifier l'utilisateur"""
    email: Optional[str] = None
    
class BrokerUpdate(BaseModel):
    """Données pour mettre à jour les clés API du broker"""
    broker_api_key: str
    broker_api_secret: str