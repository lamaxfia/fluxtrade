"""
metaapi_connector.py — Connexion broker via MetaApi (cloud).
Uniquement pour l'EXÉCUTION des ordres.
Les données de marché viennent de agent/market_data.py (Yahoo Finance).
"""
import asyncio
import inspect
import logging
from typing import Optional
from metaapi_cloud_sdk import MetaApi
from app.config import settings

logger = logging.getLogger(__name__)

METAAPI_TOKEN = settings.metaapi_token


async def _maybe_await(value):
    """Awaite si c'est un coroutine, sinon retourne tel quel"""
    if inspect.isawaitable(value):
        return await value
    return value


async def get_account(account_id: str):
    api = MetaApi(METAAPI_TOKEN)
    try:
        account = await api.metatrader_account_api.get_account(account_id)
        return api, account
    except Exception as e:
        logger.error(f"\n Erreur récupération compte MetaApi: {e}")
        return None, None


async def connect_account(account_id: str):
    """
    Connecte un compte broker via MetaApi.
    Retourne (api, account, connection) ou (None, None, None).
    """
    api, account = await get_account(account_id)
    if not account:
        return None, None, None

    try:
        if account.state != 'DEPLOYED':
            logger.info(f"\n Déploiement du compte MetaApi...")
            await account.deploy()
            await account.wait_connected()

        connection = account.get_streaming_connection()
        await connection.connect()
        await connection.wait_synchronized()

        logger.info(f"\n MetaApi connecté — compte {account_id}")
        return api, account, connection

    except Exception as e:
        logger.error(f"\n Erreur connexion MetaApi: {e}")
        return None, None, None


async def disconnect_account(api, connection):
    """Ferme proprement la connexion"""
    try:
        if connection:
            await _maybe_await(connection.close())
            logger.info(f"\n Connexion MetaApi fermée")
    except Exception as e:
        logger.warning(f"\n Erreur fermeture connexion: {e}")
    try:
        if api:
            await _maybe_await(api.close())
    except Exception as e:
        logger.warning(f"\n Erreur fermeture API: {e}")


async def resolve_symbol(connection, symbol: str) -> Optional[str]:
    """
    Trouve le vrai nom du symbole sur ce broker.
    Interroge la vraie liste des symboles du broker (terminal_state.specifications)
    plutôt que de deviner — s'adapte à tous les brokers automatiquement.
    """
    try:
        specs = connection.terminal_state.specifications
        if not specs:
            logger.warning(f"\n [Symbol] Aucune spec disponible — utilisation nom brut: {symbol}")
            return symbol

        # Construit un set des symboles disponibles
        if specs and isinstance(specs[0], dict):
            available = {s['symbol'] for s in specs}
        else:
            available = set(specs)

        # 1. Correspondance exacte
        if symbol in available:
            return symbol

        # 2. Suffixes courants broker par broker
        for suffix in ["m", ".", "+", "i", "-", "_"]:
            candidate = f"{symbol}{suffix}"
            if candidate in available:
                logger.info(f"\n [Symbol] Suffixe trouvé: {symbol} → {candidate}")
                return candidate

        # 3. Préfixes courants
        for prefix in ["#", "."]:
            candidate = f"{prefix}{symbol}"
            if candidate in available:
                logger.info(f"\n [Symbol] Préfixe trouvé: {symbol} → {candidate}")
                return candidate

        # 4. Recherche partielle (startswith, insensible à la casse)
        symbol_lower = symbol.lower()
        for s in available:
            if s.lower().startswith(symbol_lower) or symbol_lower.startswith(s.lower()):
                logger.info(f"\n [Symbol] Correspondance partielle: {symbol} → {s}")
                return s

        logger.warning(f"\n [Symbol] {symbol} introuvable sur ce broker — ignoré")
        return None

    except Exception as e:
        logger.warning(f"\n Erreur résolution symbole {symbol}: {e} — utilisation nom brut")
        return symbol


async def place_order_metaapi(
    connection,
    symbol: str,
    decision: str,
    lot_size: float,
    sl_pips: int,
    tp_pips: int,
    user_id: int,
    current_price: float = 0.0
) -> Optional[dict]:
    """
    Exécute un ordre de marché via MetaApi.
    
    current_price : prix fourni par Yahoo Finance (agent/market_data.py).
    Si fourni et > 0, calcule SL/TP. Sinon, ordre sans SL/TP (sécurisé).
    MetaApi exécute au prix du marché — pas besoin de le lui passer.
    """
    if decision == "HOLD":
        return None

    try:
        pip = 0.01 if "JPY" in symbol.upper() else 0.0001

        # Calcule SL/TP seulement si on a un prix de référence fiable
        sl = None
        tp = None
        if current_price > 0 and sl_pips > 0 and tp_pips > 0:
            if decision == "BUY":
                sl = round(current_price - sl_pips * pip, 5)
                tp = round(current_price + tp_pips * pip, 5)
            else:
                sl = round(current_price + sl_pips * pip, 5)
                tp = round(current_price - tp_pips * pip, 5)

        options = {'comment': f'FT_{user_id}', 'clientId': f'ft_{user_id}'}

        if decision == "BUY":
            kwargs = {"symbol": symbol, "volume": lot_size, "options": options}
            if sl: kwargs["stop_loss"] = sl
            if tp: kwargs["take_profit"] = tp
            result = await connection.create_market_buy_order(**kwargs)
        else:
            kwargs = {"symbol": symbol, "volume": lot_size, "options": options}
            if sl: kwargs["stop_loss"] = sl
            if tp: kwargs["take_profit"] = tp
            result = await connection.create_market_sell_order(**kwargs)

        execution_price = result.get('openPrice', result.get('price', current_price))

        logger.info(
            f"\n [{symbol}] Ordre {decision} exécuté ✅"
            f" | id: {result.get('orderId')}"
            f" | prix: {execution_price}"
            f" | SL: {sl} TP: {tp}"
        )
        return {
            "ticket":    result.get('orderId'),
            "symbol":    symbol,
            "decision":  decision,
            "price":     execution_price,
            "lot_size":  lot_size,
            "sl":        sl or 0,
            "tp":        tp or 0,
        }

    except Exception as e:
        logger.error(f"\n [{symbol}] Erreur placement ordre: {e}")
        return None


async def get_positions_metaapi(connection, user_id: int) -> list:
    """Retourne les positions ouvertes de l'utilisateur"""
    try:
        positions = connection.terminal_state.positions
        return [
            {
                "ticket":        pos['id'],
                "symbol":        pos['symbol'],
                "type":          "BUY" if pos['type'] == 'POSITION_TYPE_BUY' else "SELL",
                "lot_size":      pos['volume'],
                "open_price":    pos['openPrice'],
                "current_price": pos.get('currentPrice', pos['openPrice']),
                "sl":            pos.get('stopLoss'),
                "tp":            pos.get('takeProfit'),
                "profit":        pos.get('profit', 0),
            }
            for pos in positions
            if pos.get('clientId', '').startswith(f'ft_{user_id}')
        ]
    except Exception as e:
        logger.error(f"\n Erreur récupération positions: {e}")
        return []


async def close_position_metaapi(connection, position_id: str) -> bool:
    """Ferme une position"""
    try:
        await connection.close_position(position_id)
        logger.info(f"\n Position {position_id} fermée ✅")
        return True
    except Exception as e:
        logger.error(f"\n Erreur fermeture position {position_id}: {e}")
        return False