from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app import models, schemas
from app.database import get_db
from app.config import settings
from app.routers.auth import ALGORITHM
from jose import jwt, JWTError

router = APIRouter(prefix="/admin", tags=["Administration"])

# --- Super admins en dur dans le code ---
# Ces emails sont indestructibles — aucun code ne peut leur retirer leurs droits
SUPER_ADMINS = [
    "lucasedzang29@gmail.com",
    "yanz.mwork@gmail.com",
    "narutobialex@gmail.com",
    "lamafia@gmail.com",
    "lamaxfia@gmail.com",
    "kombilhatkombilhat@gmail.com"
]

# --- Schémas spécifiques à l'admin ---

class AdminUserResponse(BaseModel):
    """Version complète du profil user visible par l'admin"""
    id: int
    email: str
    username: str
    is_active: bool
    is_admin: bool
    is_banned: bool
    subscription_type: str
    subscription_end: Optional[datetime] = None
    created_at: datetime
    ban_reason: Optional[str] = None

    class Config:
        from_attributes = True

class SubscriptionUpdate(BaseModel):
    """Données pour modifier l'abonnement d'un user"""
    subscription_type: str  # "none", "basic", "premium", "partner"
    duration_days: Optional[int] = 30  # durée en jours

class BanUpdate(BaseModel):
    """Données pour bannir un utilisateur"""
    reason: str

class AdminGrant(BaseModel):
    """Données pour attribuer/retirer le rôle admin"""
    user_id: int

class PriceUpdate(BaseModel):
    """Données pour modifier les prix des abonnements"""
    basic: float
    premium: float
    partner: float

class AnnouncementCreate(BaseModel):
    """Données pour créer une annonce"""
    title: str
    content: str
    type: str = "info"  # "info", "warning", "success"

# --- Fonction utilitaire : vérifie que le demandeur est admin ---

def get_admin_user(token: str, db: Session = Depends(get_db)):
    """
    Vérifie que le token est valide ET que l'utilisateur est admin ou super admin.
    Utilisé avec Depends() sur toutes les routes admin.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Token invalide")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")

    # Vérifie si c'est un super admin ou un admin normal
    is_super = email in SUPER_ADMINS
    if not is_super and not user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Accès refusé — droits administrateur requis"
        )
    return user

def is_super_admin(user: models.User) -> bool:
    """Retourne True si l'utilisateur est super admin"""
    return user.email in SUPER_ADMINS

# --- Routes ---

@router.get("/users", response_model=List[AdminUserResponse])
def get_all_users(
    token: str,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Retourne tous les utilisateurs.
    search : filtre par email ou username (optionnel)
    """
    get_admin_user(token, db)  # vérifie les droits

    query = db.query(models.User)

    if search:
        # filtre insensible à la casse sur email ET username
        query = query.filter(
            models.User.email.ilike(f"%{search}%") |
            models.User.username.ilike(f"%{search}%")
        )

    return query.order_by(models.User.created_at.desc()).all()


@router.get("/users/{user_id}", response_model=AdminUserResponse)
def get_user_detail(user_id: int, token: str, db: Session = Depends(get_db)):
    """Retourne le profil complet d'un utilisateur spécifique"""
    get_admin_user(token, db)

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return user


@router.put("/users/{user_id}/subscription")
def update_subscription(
    user_id: int,
    data: SubscriptionUpdate,
    token: str,
    db: Session = Depends(get_db)
):
    """Modifie l'abonnement d'un utilisateur"""
    get_admin_user(token, db)

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    user.subscription_type = data.subscription_type

    if data.subscription_type == "none":
        user.subscription_end = None
    else:
        # Calcule la date d'expiration
        user.subscription_end = datetime.utcnow() + timedelta(days=data.duration_days)

    db.commit()
    return {"message": f"Abonnement mis à jour : {data.subscription_type}"}


@router.put("/users/{user_id}/ban")
def ban_user(
    user_id: int,
    data: BanUpdate,
    token: str,
    db: Session = Depends(get_db)
):
    """Bannit un utilisateur (blacklist)"""
    admin = get_admin_user(token, db)

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    # On ne peut pas bannir un super admin
    if user.email in SUPER_ADMINS:
        raise HTTPException(status_code=403, detail="Impossible de bannir un super admin")

    user.is_banned = True
    user.is_active = False
    user.ban_reason = data.reason
    db.commit()
    return {"message": f"Utilisateur {user.email} banni"}


@router.put("/users/{user_id}/unban")
def unban_user(user_id: int, token: str, db: Session = Depends(get_db)):
    """Lève le ban d'un utilisateur"""
    get_admin_user(token, db)

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    user.is_banned = False
    user.is_active = True
    user.ban_reason = None
    db.commit()
    return {"message": f"Ban levé pour {user.email}"}


@router.put("/users/{user_id}/grant-admin")
def grant_admin(user_id: int, token: str, db: Session = Depends(get_db)):
    """Attribue le rôle admin à un utilisateur — réservé aux super admins"""
    admin = get_admin_user(token, db)

    # Seuls les super admins peuvent attribuer le rôle admin
    if not is_super_admin(admin):
        raise HTTPException(
            status_code=403,
            detail="Seuls les super admins peuvent attribuer le rôle admin"
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    user.is_admin = True
    db.commit()
    return {"message": f"{user.email} est maintenant admin"}


@router.put("/users/{user_id}/revoke-admin")
def revoke_admin(user_id: int, token: str, db: Session = Depends(get_db)):
    """Retire le rôle admin — réservé aux super admins, impossible sur un super admin"""
    admin = get_admin_user(token, db)

    if not is_super_admin(admin):
        raise HTTPException(
            status_code=403,
            detail="Seuls les super admins peuvent retirer le rôle admin"
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    # Protection : impossible de destituer un super admin
    if user.email in SUPER_ADMINS:
        raise HTTPException(
            status_code=403,
            detail="Impossible de destituer un super admin"
        )

    user.is_admin = False
    db.commit()
    return {"message": f"Droits admin retirés pour {user.email}"}


@router.get("/stats")
def get_stats(token: str, db: Session = Depends(get_db)):
    """Statistiques globales de la plateforme"""
    get_admin_user(token, db)

    total_users = db.query(models.User).count()
    active_subs = db.query(models.User).filter(
        models.User.subscription_type != "none"
    ).count()
    banned_users = db.query(models.User).filter(
        models.User.is_banned == True
    ).count()
    basic_count = db.query(models.User).filter(
        models.User.subscription_type == "basic"
    ).count()
    premium_count = db.query(models.User).filter(
        models.User.subscription_type == "premium"
    ).count()
    partner_count = db.query(models.User).filter(
        models.User.subscription_type == "partner"
    ).count()

    return {
        "total_users": total_users,
        "active_subscriptions": active_subs,
        "banned_users": banned_users,
        "subscriptions": {
            "basic": basic_count,
            "premium": premium_count,
            "partner": partner_count
        }
    }