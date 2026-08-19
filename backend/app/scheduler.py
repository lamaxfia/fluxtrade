import threading
import time
import logging
from datetime import datetime
from app.database import SessionLocal
from app import models

logger = logging.getLogger(__name__)


def check_expired_subscriptions():
    """Vérifie toutes les heures les abonnements expirés"""
    while True:
        try:
            db = SessionLocal()

            expired_users = db.query(models.User).filter(
                models.User.subscription_type != "none",
                models.User.subscription_end < datetime.utcnow(),
                models.User.subscription_end != None
            ).all()

            for user in expired_users:
                logger.info(f"Abonnement expiré: {user.email}")
                user.subscription_type = "none"

                # Marque les trades ouverts comme expirés
                open_trades = db.query(models.Trade).filter(
                    models.Trade.user_id == user.id,
                    models.Trade.status == "open"
                ).all()

                for trade in open_trades:
                    trade.status = "expired"

                # Arrête l'agent
                from agent.trading_agent import stop_agent_for_user
                stop_agent_for_user(user.id)

            db.commit()
            db.close()

            if expired_users:
                logger.info(f"{len(expired_users)} abonnements révoqués")

        except Exception as e:
            logger.error(f"Erreur scheduler: {e}")

        time.sleep(3600)  # vérifie toutes les heures


def start_scheduler():
    thread = threading.Thread(
        target=check_expired_subscriptions,
        name="subscription_scheduler",
        daemon=True
    )
    thread.start()
    logger.info("Scheduler d'abonnements démarré")