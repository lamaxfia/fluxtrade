from typing import Optional
import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from agent.metaapi_connector import (
    connect_account, disconnect_account,
    place_order_metaapi, get_positions_metaapi,
    close_position_metaapi, resolve_symbol
)
from agent.market_data import get_market_data
from agent.risk_manager import can_open_trade

logger = logging.getLogger(__name__)

# ============================================================
# MODE TEST
# True  → BUY simple toutes les 2min (pour valider MetaApi)
# False → IA complète avec Yahoo Finance
# ============================================================
TEST_MODE = False

# ============================================================
# PAIRES PAR ABONNEMENT
# ============================================================
SYMBOLS_BY_PLAN = {
    "basic": [
        "EURUSD", "GBPUSD", "USDJPY",
        "XAUUSD",
        "SOLUSD",
    ],
    "premium": [
        "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD",
        "XAUUSD", "XAGUSD",
        "SOLUSD", "ETHUSD",
    ],
    "partner": [
        "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD",
        "AUDNZD", "EURGBP", "EURJPY",
        "XAUUSD", "XAGUSD", "XPTUSD",
        "SOLUSD", "ETHUSD", "BTCUSD",
        "AAPL", "US500",
    ],
}

INTERVAL_BY_PLAN = {
    "basic":   4 * 3600,
    "premium": 3600,
    "partner": 1800,
}

active_threads = {}


class UserTradingAgent:

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.running = False
        self.thread = None
        # Cache symboles résolus : {"EURUSD": "EURUSDm"}
        self._symbol_cache = {}

    def start(self):
        import threading
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(
            target=self._run_loop,
            name=f"agent_user_{self.user_id}",
            daemon=True
        )
        self.thread.start()
        logger.info(f"\n{'='*50}\n Agent FluxTrade démarré — user {self.user_id}\n{'='*50}")

    def stop(self):
        self.running = False
        logger.info(f"\n Agent arrêté — user {self.user_id}")

    def _run_loop(self):
        asyncio.run(self._async_run_loop())

    async def _async_run_loop(self):
        """
        Boucle principale — se connecte à MetaApi UNE SEULE FOIS par cycle,
        et uniquement quand c'est réellement nécessaire (TEST_MODE, trade à
        exécuter, ou positions ouvertes à surveiller). L'analyse Yahoo Finance
        (gratuite) se fait toujours en amont, sans connexion MetaApi.
        """
        db = SessionLocal()
        try:
            while self.running:
                user = db.query(models.User).filter(
                    models.User.id == self.user_id
                ).first()

                if not user or user.subscription_type == "none":
                    logger.info(f"\n [User {self.user_id}] Pas d'abonnement — pause 5min")
                    await asyncio.sleep(300)
                    continue

                if user.subscription_end and user.subscription_end < datetime.utcnow():
                    logger.info(f"\n [User {self.user_id}] Abonnement expiré — pause 1h")
                    await asyncio.sleep(3600)
                    continue

                if not user.broker_api_key:
                    logger.info(f"\n [User {self.user_id}] Broker non configuré — pause 5min")
                    await asyncio.sleep(300)
                    continue

                import json
                try:
                    creds = json.loads(user.broker_api_key)
                    account_id = creds.get('metaapi_account_id')
                    if not account_id:
                        await asyncio.sleep(300)
                        continue
                except Exception:
                    await asyncio.sleep(300)
                    continue

                try:
                    if TEST_MODE:
                        # Le mode test a besoin d'une connexion directe (pas d'analyse au préalable)
                        api, account, connection = await connect_account(account_id)
                        if not connection:
                            logger.error(f"\n [User {self.user_id}] Connexion échouée — pause 5min")
                            await asyncio.sleep(300)
                            continue
                        try:
                            await self._test_mode_trade(user, db, connection)
                        finally:
                            await disconnect_account(api, connection)
                    else:
                        # Analyse Yahoo Finance d'abord (gratuit) — connecte MetaApi
                        # seulement si un trade doit réellement être exécuté
                        await self._analyze_and_trade_async(user, db, account_id)

                    # Surveillance des positions ouvertes — connexion séparée,
                    # UNIQUEMENT s'il y a effectivement quelque chose à surveiller
                    open_trades_count = db.query(models.Trade).filter(
                        models.Trade.user_id == self.user_id,
                        models.Trade.status == "open"
                    ).count()

                    if open_trades_count > 0:
                        api, account, connection = await connect_account(account_id)
                        if connection:
                            try:
                                await self._monitor_loop_async(user, db, connection, duration=60)
                            finally:
                                await disconnect_account(api, connection)

                except Exception as e:
                    logger.error(f"\n [User {self.user_id}] Erreur cycle: {e}")

                interval = 120 if TEST_MODE else INTERVAL_BY_PLAN.get(user.subscription_type, 3600)
                logger.info(f"\n [User {self.user_id}] Prochain cycle dans {interval//60}min")
                await asyncio.sleep(interval)

        except Exception as e:
            logger.error(f"\n Erreur critique agent user {self.user_id}: {e}")
        finally:
            db.close()
            logger.info(f"\n [User {self.user_id}] Agent terminé — données préservées en DB")

    async def _get_real_symbol(self, connection, symbol: str) -> Optional[str]:
        """Résout et met en cache le vrai nom du symbole sur ce broker"""
        if symbol in self._symbol_cache:
            return self._symbol_cache[symbol]
        real = await resolve_symbol(connection, symbol)
        if real:
            self._symbol_cache[symbol] = real
            logger.info(f"\n [Symbol] {symbol} → {real} (résolu)")
        return real

    async def _test_mode_trade(self, user, db, connection):
        """MODE TEST — BUY simple sans IA pour valider MetaApi"""
        logger.info(f"\n [TEST MODE] User {self.user_id} — tentative BUY EURUSD")

        real_symbol = await self._get_real_symbol(connection, "EURUSD")
        if not real_symbol:
            logger.error(f"\n [TEST MODE] Symbole EURUSD introuvable sur ce broker")
            return

        # Récupère le prix Yahoo Finance pour le SL/TP
        market_data = get_market_data("EURUSD", "1h")
        current_price = market_data['close'] if market_data else 0.0

        result = await place_order_metaapi(
            connection=connection,
            symbol=real_symbol,
            decision="BUY",
            lot_size=0.01,
            sl_pips=50,
            tp_pips=100,
            user_id=user.id,
            current_price=current_price
        )

        if result:
            trade = models.Trade(
                user_id=user.id,
                symbol=real_symbol,
                direction="BUY",
                lot_size=0.01,
                open_price=result['price'],
                sl=result['sl'],
                tp=result['tp'],
                ticket=str(result['ticket']),
                status="open",
                confidence=1.0,
                analysis_type="test_mode",
                reason="Mode test — BUY automatique",
            )
            db.add(trade)
            db.commit()
            logger.info(f"\n [TEST MODE] ✅ Trade ouvert — ticket: {result['ticket']} prix: {result['price']}")
        else:
            logger.error(f"\n [TEST MODE] ❌ Ordre échoué")

    async def _analyze_and_trade_async(self, user, db, account_id):
        """
        Phase 1 : Analyse Yahoo Finance + IA (AUCUNE connexion MetaApi).
        Phase 2 : Une seule connexion MetaApi, ouverte uniquement si au
        moins un trade doit être exécuté.
        """
        from agent.ai_engine import make_trading_decision

        symbols = SYMBOLS_BY_PLAN.get(user.subscription_type, ["EURUSD"])
        timeframe = {
            "basic":   "4h",
            "premium": "1h",
            "partner": "30m"
        }.get(user.subscription_type, "1h")

        # ── PHASE 1 : Analyse complète SANS MetaApi ──
        trades_to_execute = []

        for symbol in symbols:
            try:
                can_trade, reason = can_open_trade(user, symbol, db)
                if not can_trade:
                    logger.info(f"\n [{symbol}] Trade bloqué: {reason}")
                    continue

                market_data = get_market_data(symbol, timeframe)
                if not market_data:
                    logger.warning(f"\n [{symbol}] Données Yahoo Finance indisponibles — ignoré")
                    continue

                decision = make_trading_decision(
                    symbol=symbol,
                    market_data=market_data,
                    subscription_type=user.subscription_type
                )

                logger.info(
                    f"\n [{symbol}] Décision: {decision['decision']}"
                    f" | Confiance: {decision['confidence']}"
                    f" | Source: {decision.get('source', '?')}"
                )

                if decision['decision'] == 'HOLD' or decision['confidence'] < 0.6:
                    logger.info(f"\n [{symbol}] HOLD — pas de trade")
                    continue

                trades_to_execute.append((symbol, decision, market_data['close']))

            except Exception as e:
                logger.error(f"\n Erreur analyse {symbol}: {e}")
                continue

        if not trades_to_execute:
            logger.info(f"\n [User {self.user_id}] Aucun trade à exécuter — MetaApi non sollicité")
            return

        # ── PHASE 2 : UNE seule connexion MetaApi pour exécuter tous les trades ──
        logger.info(f"\n [User {self.user_id}] {len(trades_to_execute)} trade(s) à exécuter — connexion MetaApi...")

        api, account, connection = await connect_account(account_id)
        if not connection:
            logger.error(f"\n [User {self.user_id}] Connexion MetaApi échouée — trades annulés")
            return

        try:
            for symbol, decision, close_price in trades_to_execute:
                try:
                    real_symbol = await self._get_real_symbol(connection, symbol)
                    if not real_symbol:
                        logger.warning(f"\n [{symbol}] Symbole introuvable sur le broker — ignoré")
                        continue

                    order_result = await place_order_metaapi(
                        connection=connection,
                        symbol=real_symbol,
                        decision=decision['decision'],
                        lot_size=decision['lot_size'],
                        sl_pips=decision['sl_pips'],
                        tp_pips=decision['tp_pips'],
                        user_id=user.id,
                        current_price=close_price
                    )

                    if order_result:
                        trade = models.Trade(
                            user_id=user.id,
                            symbol=real_symbol,
                            direction=decision['decision'],
                            lot_size=decision['lot_size'],
                            open_price=order_result['price'],
                            sl=order_result['sl'],
                            tp=order_result['tp'],
                            ticket=str(order_result['ticket']),
                            status="open",
                            confidence=decision['confidence'],
                            analysis_type=decision['analysis_type'],
                            reason=decision.get('reason', ''),
                        )
                        db.add(trade)
                        db.commit()
                        logger.info(f"\n [{real_symbol}] ✅ Trade enregistré — ticket: {order_result['ticket']}")

                except Exception as e:
                    logger.error(f"\n Erreur exécution {symbol}: {e}")
                    continue
        finally:
            await disconnect_account(api, connection)

    async def _monitor_loop_async(self, user, db, connection, duration=60):
        """Surveille les positions ouvertes"""
        loop = asyncio.get_event_loop()
        end_time = loop.time() + duration
        logger.info(f"\n [Monitor] User {self.user_id} — surveillance {duration}s")

        while loop.time() < end_time and self.running:
            try:
                positions = await get_positions_metaapi(connection, user.id)

                for pos in positions:
                    trade = db.query(models.Trade).filter(
                        models.Trade.ticket == str(pos['ticket']),
                        models.Trade.status == "open"
                    ).first()

                    if trade:
                        trade.profit = pos['profit']
                        trade.current_price = pos['current_price']

                        if pos.get('tp') and pos.get('current_price'):
                            tp_hit = (
                                trade.direction == 'BUY' and
                                pos['current_price'] >= pos['tp']
                            ) or (
                                trade.direction == 'SELL' and
                                pos['current_price'] <= pos['tp']
                            )
                            if tp_hit:
                                closed = await close_position_metaapi(
                                    connection, str(pos['ticket'])
                                )
                                if closed:
                                    trade.status = "closed"
                                    trade.close_price = pos['current_price']
                                    trade.closed_at = datetime.utcnow()
                                    logger.info(
                                        f"\n [Monitor] ✅ TP atteint — ticket {pos['ticket']}"
                                        f" profit: {pos['profit']}"
                                    )
                        db.commit()

            except Exception as e:
                logger.error(f"\n [Monitor] Erreur: {e}")

            await asyncio.sleep(10)


# ============================================================
# GESTIONNAIRE GLOBAL
# ============================================================

def start_agent_for_user(user_id: int):
    if user_id not in active_threads:
        agent = UserTradingAgent(user_id)
        agent.start()
        active_threads[user_id] = agent


def stop_agent_for_user(user_id: int):
    if user_id in active_threads:
        active_threads[user_id].stop()
        del active_threads[user_id]


def start_all_active_agents():
    db = SessionLocal()
    try:
        active_users = db.query(models.User).filter(
            models.User.subscription_type != "none",
            models.User.is_active == True,
            models.User.is_banned == False,
            models.User.broker_api_key != None
        ).all()

        for user in active_users:
            if user.subscription_end and user.subscription_end < datetime.utcnow():
                continue
            start_agent_for_user(user.id)
            logger.info(f"\n Agent démarré — {user.email} ({user.subscription_type})")

        logger.info(f"\n {'='*40}\n {len(active_threads)} agents actifs au démarrage\n {'='*40}")
    finally:
        db.close()