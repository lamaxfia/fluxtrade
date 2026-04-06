import time
import logging
import threading
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from agent.ai_engine import make_trading_decision
from agent.mt5_connector import (
    connect_mt5, disconnect_mt5, get_market_data,
    place_order, monitor_positions, close_position_if_target_reached
)
from agent.risk_manager import can_open_trade, MAX_TRADES

logger = logging.getLogger(__name__)

# Symboles disponibles par abonnement
SYMBOLS_BY_PLAN = {
    "basic":   ["EURUSD", "GBPUSD", "USDJPY"],
    "premium": ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD"],
    "partner": ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD",
                "ETHUSD", "USDCHF", "AUDUSD", "NZDUSD", "US500"],
}

# Intervalle d'analyse en secondes selon l'abonnement
INTERVAL_BY_PLAN = {
    "basic":   4 * 3600,   # toutes les 4h
    "premium": 3600,       # toutes les 1h
    "partner": 1800,       # toutes les 30min
}

# Threads actifs par user_id (pour éviter les doublons)
active_threads = {}


class UserTradingAgent:
    """
    Agent de trading individuel pour un utilisateur.
    Tourne dans son propre thread et gère tous ses trades.
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.running = False
        self.thread = None

    def start(self):
        """Démarre l'agent dans un thread séparé"""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(
            target=self._run_loop,
            name=f"agent_user_{self.user_id}",
            daemon=True  # s'arrête avec le serveur principal
        )
        self.thread.start()
        logger.info(f"Agent démarré pour user {self.user_id}")

    def stop(self):
        """Arrête l'agent proprement"""
        self.running = False
        logger.info(f"Agent arrêté pour user {self.user_id}")

    def _run_loop(self):
        """Boucle principale de l'agent"""
        db = SessionLocal()
        try:
            while self.running:
                user = db.query(models.User).filter(
                    models.User.id == self.user_id
                ).first()

                if not user or user.subscription_type == "none":
                    logger.info(f"User {self.user_id} sans abonnement — agent en pause")
                    time.sleep(300)  # vérifie toutes les 5min
                    continue

                # Vérifie l'abonnement
                if user.subscription_end and user.subscription_end < datetime.utcnow():
                    logger.info(f"User {self.user_id} — abonnement expiré")
                    time.sleep(3600)
                    continue

                # Connexion MT5
                if not user.broker_api_key:
                    time.sleep(300)
                    continue

                # Parse les credentials MT5 (stockés en JSON dans broker_api_key)
                import json
                try:
                    creds = json.loads(user.broker_api_key)
                    connected = connect_mt5(
                        login=int(creds['login']),
                        password=creds['password'],
                        server=creds['server']
                    )
                except Exception as e:
                    logger.error(f"Erreur connexion MT5 user {self.user_id}: {e}")
                    time.sleep(300)
                    continue

                if not connected:
                    time.sleep(300)
                    continue

                try:
                    # Analyse et trading
                    self._analyze_and_trade(user, db)

                    # Surveillance des positions ouvertes (toutes les 10 secondes)
                    self._monitor_loop(user, db, duration=60)

                finally:
                    disconnect_mt5()

                # Attente avant prochain cycle
                interval = INTERVAL_BY_PLAN.get(user.subscription_type, 3600)
                logger.info(f"User {self.user_id} — prochain cycle dans {interval//60}min")
                time.sleep(interval)

        except Exception as e:
            logger.error(f"Erreur critique agent user {self.user_id}: {e}")
        finally:
            db.close()

    def _analyze_and_trade(self, user: models.User, db: Session):
        """Lance l'analyse et exécute les trades pour tous les symboles"""
        symbols = SYMBOLS_BY_PLAN.get(user.subscription_type, ["EURUSD"])

        for symbol in symbols:
            try:
                # Vérifie si on peut ouvrir un trade
                can_trade, reason = can_open_trade(user, symbol, db)
                if not can_trade:
                    logger.info(f"[{symbol}] Trade bloqué: {reason}")
                    continue

                # Récupère les données de marché
                timeframe = {
                    "basic": 240,    # 4H
                    "premium": 60,   # 1H
                    "partner": 30    # 30min
                }.get(user.subscription_type, 60)

                market_data = get_market_data(symbol, timeframe)
                if not market_data:
                    continue

                # Décision IA
                decision = make_trading_decision(
                    symbol=symbol,
                    market_data=market_data,
                    subscription_type=user.subscription_type
                )

                logger.info(f"[{symbol}] Décision: {decision['decision']} "
                           f"(conf: {decision['confidence']})")

                # N'exécute que si confiance > 60%
                if decision['decision'] == 'HOLD' or decision['confidence'] < 0.6:
                    continue

                # Exécute l'ordre sur MT5
                order_result = place_order(
                    symbol=symbol,
                    decision=decision['decision'],
                    lot_size=decision['lot_size'],
                    sl_pips=decision['sl_pips'],
                    tp_pips=decision['tp_pips'],
                    user_id=user.id,
                    comment=f"FluxTrade_{user.subscription_type}"
                )

                if order_result:
                    # Sauvegarde le trade en base de données
                    trade = models.Trade(
                        user_id=user.id,
                        symbol=symbol,
                        direction=decision['decision'],
                        lot_size=decision['lot_size'],
                        open_price=order_result['price'],
                        sl=order_result['sl'],
                        tp=order_result['tp'],
                        ticket=order_result['ticket'],
                        status="open",
                        confidence=decision['confidence'],
                        analysis_type=decision['analysis_type'],
                        reason=decision.get('reason', ''),
                    )
                    db.add(trade)
                    db.commit()

            except Exception as e:
                logger.error(f"Erreur analyse {symbol}: {e}")
                continue

    def _monitor_loop(self, user: models.User, db: Session, duration: int = 60):
        """
        Surveille les positions ouvertes pendant 'duration' secondes.
        Ferme instantanément si le TP est atteint.
        """
        end_time = time.time() + duration
        while time.time() < end_time and self.running:
            positions = monitor_positions(user.id)

            for pos in positions:
                # Vérifie si le TP est atteint
                closed = close_position_if_target_reached(
                    ticket=pos['ticket'],
                    profit_target=pos['profit'] * 0.95  # 95% du TP = on sécurise
                )

                if closed:
                    # Met à jour le trade en base de données
                    trade = db.query(models.Trade).filter(
                        models.Trade.ticket == pos['ticket']
                    ).first()
                    if trade:
                        trade.status = "closed"
                        trade.close_price = pos['current_price']
                        trade.profit = pos['profit']
                        trade.closed_at = datetime.utcnow()
                        db.commit()

                # Met à jour le profit en temps réel dans la DB
                trade = db.query(models.Trade).filter(
                    models.Trade.ticket == pos['ticket'],
                    models.Trade.status == "open"
                ).first()
                if trade:
                    trade.profit = pos['profit']
                    trade.current_price = pos['current_price']
                    db.commit()

            time.sleep(10)  # vérifie toutes les 10 secondes


# ============================================================
# GESTIONNAIRE GLOBAL — Démarre/arrête les agents
# ============================================================

def start_agent_for_user(user_id: int):
    """Démarre un agent pour un utilisateur s'il n'en a pas déjà un"""
    if user_id not in active_threads:
        agent = UserTradingAgent(user_id)
        agent.start()
        active_threads[user_id] = agent


def stop_agent_for_user(user_id: int):
    """Arrête l'agent d'un utilisateur"""
    if user_id in active_threads:
        active_threads[user_id].stop()
        del active_threads[user_id]


def start_all_active_agents():
    """
    Démarre les agents pour tous les utilisateurs abonnés au démarrage du serveur.
    Appelée une fois dans main.py au lancement.
    """
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        active_users = db.query(models.User).filter(
            models.User.subscription_type != "none",
            models.User.is_active == True,
            models.User.is_banned == False,
            models.User.broker_api_key != None
        ).all()

        for user in active_users:
            # Vérifie que l'abonnement n'est pas expiré
            if user.subscription_end and user.subscription_end < datetime.utcnow():
                continue
            start_agent_for_user(user.id)
            logger.info(f"Agent démarré pour {user.email} ({user.subscription_type})")

        logger.info(f"{len(active_threads)} agents de trading actifs")
    finally:
        db.close()