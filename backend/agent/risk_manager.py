import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app import models

logger = logging.getLogger(__name__)

# Limites de trades simultanés par abonnement
MAX_TRADES = {
    "basic": 3,
    "premium": 5,
    "partner": 10
}

# Perte maximale journalière autorisée (en % du capital)
MAX_DAILY_LOSS_PCT = {
    "basic": 0.03,    # 3% max par jour
    "premium": 0.05,  # 5%
    "partner": 0.08   # 8%
}


def can_open_trade(user: models.User, symbol: str, db: Session) -> tuple[bool, str]:
    """
    Vérifie toutes les conditions avant d'ouvrir un trade.
    Retourne (True, "") si OK, (False, "raison") si bloqué.
    """

    # 1 — Abonnement actif ?
    if user.subscription_type == "none":
        return False, "Aucun abonnement actif"

    # 2 — Abonnement expiré ?
    if user.subscription_end and user.subscription_end < datetime.utcnow():
        return False, "Abonnement expiré"

    # 3 — Broker configuré ?
    if not user.broker_api_key:
        return False, "Clés broker non configurées"

    # 4 — Limite de trades simultanés atteinte ?
    max_trades = MAX_TRADES.get(user.subscription_type, 3)
    active_trades = db.query(models.Trade).filter(
        models.Trade.user_id == user.id,
        models.Trade.status == "open"
    ).count()

    if active_trades >= max_trades:
        return False, f"Limite de {max_trades} trades simultanés atteinte"

    # 5 — Déjà un trade ouvert sur ce symbole ?
    existing = db.query(models.Trade).filter(
        models.Trade.user_id == user.id,
        models.Trade.symbol == symbol,
        models.Trade.status == "open"
    ).first()

    if existing:
        return False, f"Trade déjà ouvert sur {symbol}"

    return True, ""


def calculate_lot_size(
    balance: float,
    risk_pct: float,
    sl_pips: int,
    pip_value: float,
    max_lot: float
) -> float:
    """
    Calcule le lot size optimal selon le capital et le risque accepté.
    Formule standard de gestion du risque forex.

    risk_pct : pourcentage du capital à risquer par trade (ex: 0.02 = 2%)
    """
    if sl_pips == 0 or pip_value == 0:
        return 0.01

    risk_amount = balance * risk_pct
    lot = risk_amount / (sl_pips * pip_value * 100000)
    lot = round(min(lot, max_lot), 2)
    return max(lot, 0.01)  # minimum 0.01 lot