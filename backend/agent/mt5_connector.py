import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# ============================================================
# CONNEXION MT5
# ============================================================

def connect_mt5(login: int, password: str, server: str) -> bool:
    """
    Ouvre la connexion à MetaTrader 5.
    login, password, server = les infos du compte broker de l'utilisateur.
    Retourne True si connexion réussie.
    """
    if not mt5.initialize():
        logger.error("MT5 ne peut pas s'initialiser — est-il installé ?")
        return False

    authorized = mt5.login(login=login, password=password, server=server)
    if not authorized:
        logger.error(f"Connexion MT5 échouée: {mt5.last_error()}")
        mt5.shutdown()
        return False

    info = mt5.account_info()
    logger.info(f"MT5 connecté — Compte: {info.login} | Balance: {info.balance} {info.currency}")
    return True


def disconnect_mt5():
    """Ferme proprement la connexion MT5"""
    mt5.shutdown()
    logger.info("MT5 déconnecté")


# ============================================================
# RÉCUPÉRATION DES DONNÉES DE MARCHÉ
# ============================================================

def get_market_data(symbol: str, timeframe_minutes: int = 60, bars: int = 100) -> Optional[dict]:
    """
    Récupère les données OHLCV et calcule les indicateurs techniques.
    Tout est calculé localement — aucun token IA dépensé ici.

    timeframe_minutes: 60 = 1H, 240 = 4H, 30 = 30min
    bars: nombre de bougies à analyser
    """

    # Conversion du timeframe en constante MT5
    tf_map = {
        1: mt5.TIMEFRAME_M1,
        5: mt5.TIMEFRAME_M5,
        15: mt5.TIMEFRAME_M15,
        30: mt5.TIMEFRAME_M30,
        60: mt5.TIMEFRAME_H1,
        240: mt5.TIMEFRAME_H4,
        1440: mt5.TIMEFRAME_D1,
    }
    timeframe = tf_map.get(timeframe_minutes, mt5.TIMEFRAME_H1)

    # Récupère les bougies depuis MT5
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    if rates is None or len(rates) == 0:
        logger.error(f"Impossible de récupérer les données pour {symbol}")
        return None

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')

    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    volume = df['tick_volume'].values

    # ── Moyennes mobiles ──
    sma20 = float(pd.Series(close).rolling(20).mean().iloc[-1])
    sma50 = float(pd.Series(close).rolling(50).mean().iloc[-1])

    # ── RSI 14 ──
    delta = pd.Series(close).diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = float(100 - (100 / (1 + rs.iloc[-1])))

    # ── MACD (12, 26, 9) ──
    ema12 = pd.Series(close).ewm(span=12).mean()
    ema26 = pd.Series(close).ewm(span=26).mean()
    macd_line = float((ema12 - ema26).iloc[-1])
    macd_signal = float((ema12 - ema26).ewm(span=9).mean().iloc[-1])

    # ── Bandes de Bollinger (20, 2) ──
    sma20_series = pd.Series(close).rolling(20).mean()
    std20 = pd.Series(close).rolling(20).std()
    bb_upper = float((sma20_series + 2 * std20).iloc[-1])
    bb_lower = float((sma20_series - 2 * std20).iloc[-1])

    # ── Tendance 4H ──
    if close[-1] > sma20 and close[-1] > sma50:
        trend = "HAUSSIER"
    elif close[-1] < sma20 and close[-1] < sma50:
        trend = "BAISSIER"
    else:
        trend = "NEUTRE"

    # ── Support et Résistance (pivots simples) ──
    recent_high = float(np.max(high[-20:]))
    recent_low = float(np.min(low[-20:]))

    return {
        "symbol": symbol,
        "close": round(float(close[-1]), 5),
        "open": round(float(df['open'].iloc[-1]), 5),
        "high": round(float(high[-1]), 5),
        "low": round(float(low[-1]), 5),
        "volume": int(volume[-1]),
        "sma20": round(sma20, 5),
        "sma50": round(sma50, 5),
        "rsi": round(rsi, 2),
        "macd": round(macd_line, 5),
        "macd_signal": round(macd_signal, 5),
        "bb_upper": round(bb_upper, 5),
        "bb_lower": round(bb_lower, 5),
        "trend_4h": trend,
        "support": round(recent_low, 5),
        "resistance": round(recent_high, 5),
    }


# ============================================================
# EXÉCUTION DES ORDRES
# ============================================================

def get_pip_value(symbol: str) -> float:
    """Retourne la valeur d'un pip pour ce symbole"""
    info = mt5.symbol_info(symbol)
    if info is None:
        return 0.0001  # valeur par défaut forex
    return info.point * 10 if "JPY" not in symbol else info.point * 100


def place_order(
    symbol: str,
    decision: str,
    lot_size: float,
    sl_pips: int,
    tp_pips: int,
    user_id: int,
    comment: str = "FluxTrade"
) -> Optional[dict]:
    """
    Envoie un ordre d'achat ou de vente sur MT5.
    Retourne les détails de l'ordre si succès, None si échec.
    """
    if decision == "HOLD":
        return None  # on ne fait rien

    # Récupère le prix actuel
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        logger.error(f"Impossible d'obtenir le tick pour {symbol}")
        return None

    pip = get_pip_value(symbol)

    if decision == "BUY":
        order_type = mt5.ORDER_TYPE_BUY
        price = tick.ask
        sl = price - (sl_pips * pip)
        tp = price + (tp_pips * pip)
    else:  # SELL
        order_type = mt5.ORDER_TYPE_SELL
        price = tick.bid
        sl = price + (sl_pips * pip)
        tp = price - (tp_pips * pip)

    # Construction de la requête d'ordre
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": order_type,
        "price": price,
        "sl": round(sl, 5),
        "tp": round(tp, 5),
        "deviation": 10,          # slippage max accepté (en points)
        "magic": user_id,         # on utilise user_id comme magic number pour identifier nos trades
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,    # Good Till Cancelled
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logger.error(f"Ordre {decision} {symbol} échoué: {result.comment}")
        return None

    logger.info(f"Ordre {decision} {symbol} exécuté — ticket: {result.order}")
    return {
        "ticket": result.order,
        "symbol": symbol,
        "decision": decision,
        "price": price,
        "lot_size": lot_size,
        "sl": round(sl, 5),
        "tp": round(tp, 5),
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
    }


# ============================================================
# SURVEILLANCE DES POSITIONS (temps réel)
# ============================================================

def monitor_positions(user_id: int) -> list:
    """
    Retourne toutes les positions ouvertes de cet utilisateur.
    Appelée en boucle pour surveiller les trades en cours.
    Le magic number = user_id permet de filtrer nos trades.
    """
    positions = mt5.positions_get()
    if positions is None:
        return []

    user_positions = []
    for pos in positions:
        if pos.magic == user_id:
            user_positions.append({
                "ticket": pos.ticket,
                "symbol": pos.symbol,
                "type": "BUY" if pos.type == 0 else "SELL",
                "lot_size": pos.volume,
                "open_price": pos.price_open,
                "current_price": pos.price_current,
                "sl": pos.sl,
                "tp": pos.tp,
                "profit": pos.profit,
                "open_time": datetime.fromtimestamp(pos.time).isoformat(),
            })

    return user_positions


def close_position_if_target_reached(ticket: int, profit_target: float) -> bool:
    """
    Ferme instantanément une position si le profit cible est atteint.
    C'est la fonction de sortie rapide — appelée à chaque tick de prix.
    """
    positions = mt5.positions_get(ticket=ticket)
    if not positions:
        return False

    pos = positions[0]

    # Si le profit actuel dépasse notre cible → on ferme immédiatement
    if pos.profit >= profit_target:
        close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
        tick = mt5.symbol_info_tick(pos.symbol)
        price = tick.bid if pos.type == 0 else tick.ask

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": close_type,
            "position": ticket,
            "price": price,
            "deviation": 10,
            "magic": pos.magic,
            "comment": "FluxTrade_TP_atteint",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"Position {ticket} fermée — profit: {pos.profit}")
            return True

    return False