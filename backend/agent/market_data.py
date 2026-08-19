"""
market_data.py — Données de marché via Yahoo Finance (gratuit, sans quota).
Complètement indépendant du broker — fonctionne avec MetaApi, MT5, ou n'importe quoi d'autre.
"""
import logging
import pandas as pd
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)

# ============================================================
# Correspondance symboles FluxTrade → tickers Yahoo Finance
# ============================================================
YFINANCE_TICKER_MAP = {
    # Forex
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "USDCHF": "USDCHF=X",
    "AUDUSD": "AUDUSD=X",
    "NZDUSD": "NZDUSD=X",
    "AUDNZD": "AUDNZD=X",
    "EURGBP": "EURGBP=X",
    "EURJPY": "EURJPY=X",
    # Métaux
    "XAUUSD": "GC=F",       # Or (Gold futures)
    "XAGUSD": "SI=F",       # Argent (Silver futures)
    "XPTUSD": "PL=F",       # Platine (Platinum futures)
    # Crypto
    "SOLUSD": "SOL-USD",
    "ETHUSD": "ETH-USD",
    "BTCUSD": "BTC-USD",
    # Actions tech
    "AAPL":   "AAPL",
    # Indices
    "US500":  "^GSPC",      # S&P 500
}

# Correspondance timeframe FluxTrade → intervalle yfinance
TIMEFRAME_MAP = {
    "4h":  ("5d",  "1h"),   # 5 jours de données, bougies 1h (yfinance n'a pas de 4h natif)
    "1h":  ("5d",  "1h"),
    "30m": ("2d",  "30m"),
    "10m": ("1d",  "10m"),
}


def get_market_data(symbol: str, timeframe: str = "1h") -> Optional[dict]:
    """
    Récupère les données de marché depuis Yahoo Finance et calcule les indicateurs.
    
    symbol   : nom FluxTrade standard (ex: "EURUSD", "XAUUSD", "BTCUSD")
    timeframe: "4h", "1h", "30m", "10m"
    
    Retourne un dict compatible avec ai_engine.make_trading_decision().
    Retourne None si les données sont indisponibles.
    """
    try:
        import yfinance as yf
    except ImportError:
        logger.error("\n yfinance non installé — lance: pip install yfinance")
        return None

    ticker = YFINANCE_TICKER_MAP.get(symbol)
    if not ticker:
        logger.warning(f"\n [{symbol}] Symbole inconnu dans YFINANCE_TICKER_MAP — ignoré")
        return None

    period, interval = TIMEFRAME_MAP.get(timeframe, ("5d", "1h"))

    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)

        if df is None or len(df) < 50:
            logger.warning(f"\n [{symbol}] Données insuffisantes depuis Yahoo Finance ({len(df) if df is not None else 0} bougies)")
            return None

        # Normalise les colonnes (yfinance peut retourner MultiIndex)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close = df['Close'].values.astype(float)
        high  = df['High'].values.astype(float)
        low   = df['Low'].values.astype(float)
        volume = df['Volume'].values.astype(float) if 'Volume' in df.columns else np.zeros(len(close))

        # ── Moyennes mobiles ──
        sma20 = float(pd.Series(close).rolling(20).mean().iloc[-1])
        sma50 = float(pd.Series(close).rolling(min(50, len(close))).mean().iloc[-1])

        # ── RSI 14 ──
        delta = pd.Series(close).diff()
        gain  = delta.where(delta > 0, 0).rolling(14).mean()
        loss  = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs    = gain / loss.replace(0, 1e-10)
        rsi   = float(100 - (100 / (1 + rs.iloc[-1])))

        # ── MACD (12, 26, 9) ──
        ema12       = pd.Series(close).ewm(span=12).mean()
        ema26       = pd.Series(close).ewm(span=26).mean()
        macd_line   = float((ema12 - ema26).iloc[-1])
        macd_signal = float((ema12 - ema26).ewm(span=9).mean().iloc[-1])

        # ── Bandes de Bollinger (20, 2) ──
        sma20_s  = pd.Series(close).rolling(20).mean()
        std20    = pd.Series(close).rolling(20).std()
        bb_upper = float((sma20_s + 2 * std20).iloc[-1])
        bb_lower = float((sma20_s - 2 * std20).iloc[-1])

        # ── Tendance ──
        trend = (
            "HAUSSIER" if close[-1] > sma20 and close[-1] > sma50
            else "BAISSIER" if close[-1] < sma20 and close[-1] < sma50
            else "NEUTRE"
        )

        logger.info(
            f"\n [{symbol}] Yahoo Finance OK — "
            f"close={round(float(close[-1]), 5)} RSI={round(rsi, 1)} trend={trend}"
        )

        return {
            "symbol": symbol,
            "close":       round(float(close[-1]), 5),
            "open":        round(float(df['Open'].values[-1]), 5),
            "high":        round(float(high[-1]), 5),
            "low":         round(float(low[-1]), 5),
            "volume":      int(volume[-1]),
            "sma20":       round(sma20, 5),
            "sma50":       round(sma50, 5),
            "rsi":         round(rsi, 2),
            "macd":        round(macd_line, 5),
            "macd_signal": round(macd_signal, 5),
            "bb_upper":    round(bb_upper, 5),
            "bb_lower":    round(bb_lower, 5),
            "trend_4h":    trend,
            "support":     round(float(np.min(low[-20:])), 5),
            "resistance":  round(float(np.max(high[-20:])), 5),
        }

    except Exception as e:
        logger.error(f"\n [{symbol}] Erreur Yahoo Finance: {e}")
        return None