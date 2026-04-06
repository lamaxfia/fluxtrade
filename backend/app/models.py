# Column, String, etc. = les types de colonnes SQL traduits en Python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text
from sqlalchemy.sql import func   # func.now() = l'heure actuelle côté DB
from app.database import Base

# Chaque classe = une table dans la base de données
# "User" devient la table "users" automatiquement
class User(Base):
    __tablename__ = "users"

    # Chaque attribut = une colonne
    id = Column(Integer, primary_key=True, index=True)
    # primary_key : identifiant unique de chaque ligne
    # index : accélère les recherches sur ce champ

    email = Column(String, unique=True, index=True, nullable=False)
    # unique : deux utilisateurs ne peuvent pas avoir le même email
    # nullable=False : ce champ est obligatoire

    username = Column(String, unique=True, index=True, nullable=False)

    hashed_password = Column(String, nullable=False)
    # On ne stocke JAMAIS le mot de passe en clair, seulement son "empreinte"

    is_active = Column(Boolean, default=True)
    # False = compte suspendu par un admin

    is_admin = Column(Boolean, default=False)
    # True = accès au panel admin

    subscription_type = Column(String, default="none")
    # "none", "basic", "pro", "elite" — les niveaux d'abonnement

    subscription_end = Column(DateTime, nullable=True)
    # Date d'expiration de l'abonnement (null = pas d'abonnement actif)

    broker_api_key = Column(String, nullable=True)
    # Clé API du broker fournie par l'utilisateur

    broker_api_secret = Column(String, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    # server_default : la date est générée par la base de données elle-même

    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    # onupdate : se met à jour automatiquement à chaque modification

    is_banned = Column(Boolean, default=False)
    
    ban_reason = Column(String, nullable=True)

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    symbol = Column(String, nullable=False)
    direction = Column(String, nullable=False)       # BUY ou SELL
    lot_size = Column(Float, nullable=False)
    open_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=True)
    current_price = Column(Float, nullable=True)
    sl = Column(Float, nullable=False)
    tp = Column(Float, nullable=False)
    ticket = Column(Integer, nullable=True)          # ticket MT5
    status = Column(String, default="open")          # open, closed
    profit = Column(Float, default=0.0)
    confidence = Column(Float, nullable=True)
    analysis_type = Column(String, nullable=True)
    reason = Column(String, nullable=True)
    opened_at = Column(DateTime, server_default=func.now())
    closed_at = Column(DateTime, nullable=True)