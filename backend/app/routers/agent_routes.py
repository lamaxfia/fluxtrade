from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.config import settings
from app.routers.auth import ALGORITHM
from jose import jwt, JWTError
from agent.trading_agent import (
    start_agent_for_user,
    stop_agent_for_user,
    active_threads
)

router = APIRouter(prefix="/agent", tags=["Agent"])


def get_user_from_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Token invalide")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expiré")
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return user


@router.post("/start")
def start_agent(token: str, db: Session = Depends(get_db)):
    """Démarre l'agent de trading pour l'utilisateur connecté"""
    user = get_user_from_token(token, db)

    if user.subscription_type == "none":
        raise HTTPException(
            status_code=403,
            detail="Abonnement requis pour démarrer le bot"
        )
    if not user.broker_api_key:
        raise HTTPException(
            status_code=400,
            detail="Broker non configuré — va dans Paramètres"
        )

    start_agent_for_user(user.id)
    return {"message": f"Agent démarré pour {user.username}"}


@router.post("/stop")
def stop_agent(token: str, db: Session = Depends(get_db)):
    """Arrête l'agent de trading"""
    user = get_user_from_token(token, db)
    stop_agent_for_user(user.id)
    return {"message": "Agent arrêté"}


@router.get("/status")
def agent_status(token: str, db: Session = Depends(get_db)):
    """Retourne le statut de l'agent"""
    user = get_user_from_token(token, db)
    is_running = user.id in active_threads
    return {
        "running": is_running,
        "subscription": user.subscription_type,
        "broker_configured": bool(user.broker_api_key),
    }