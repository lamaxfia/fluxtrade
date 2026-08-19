import os
import json
import time
import logging
from typing import Optional
from dotenv import load_dotenv

# Charge le fichier .env AVANT d'initialiser les clients
load_dotenv()

from groq import Groq
from google import genai
from openai import OpenAI  # DeepSeek et OpenRouter utilisent le format OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURATION DES CLIENTS IA
# ============================================================

# Groq — analyse technique principale
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Gemini — analyse fondamentale (accès web)

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# DeepSeek — via leur API compatible OpenAI
deepseek_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# Mistral — fallback technique
mistral_client = OpenAI(
    api_key=os.getenv("MISTRAL_API_KEY"),
    base_url="https://api.mistral.ai/v1"
)

# OpenRouter — fallback universel
openrouter_client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# ============================================================
# PROMPTS ULTRA-COMPACTS (économie de tokens)
# ============================================================

def build_technical_prompt(symbol: str, data: dict) -> str:
    """
    Prompt minimaliste pour l'analyse technique.
    On envoie uniquement les chiffres essentiels — pas de texte inutile.
    Chaque token économisé = argent économisé à l'échelle.
    """
    return f"""Analyse technique forex/CFD. Réponds UNIQUEMENT en JSON valide.

Symbole: {symbol}
Prix actuel: {data['close']}
SMA20: {data.get('sma20', 'N/A')} | SMA50: {data.get('sma50', 'N/A')}
RSI14: {data.get('rsi', 'N/A')}
MACD: {data.get('macd', 'N/A')} | Signal: {data.get('macd_signal', 'N/A')}
BB_upper: {data.get('bb_upper', 'N/A')} | BB_lower: {data.get('bb_lower', 'N/A')}
Volume: {data.get('volume', 'N/A')}
Tendance 4h: {data.get('trend_4h', 'N/A')}
Support: {data.get('support', 'N/A')} | Résistance: {data.get('resistance', 'N/A')}

JSON requis (rien d'autre):
{{"decision":"BUY|SELL|HOLD","confidence":0.0-1.0,"sl_pips":int,"tp_pips":int,"lot_size":0.01-1.0,"reason":"max 20 mots"}}"""


def build_fundamental_prompt(symbol: str, technical_result: dict) -> str:
    """
    Prompt fondamental — Gemini a accès au web donc on lui demande
    d'aller chercher l'actualité récente. Plus long mais utilisé rarement.
    """
    return f"""Tu es un analyste forex senior. Analyse fondamentale pour {symbol}.

Recherche: actualités économiques récentes, calendrier économique du jour,
sentiment de marché, politique des banques centrales concernées.

Analyse technique déjà faite: {json.dumps(technical_result)}

Ta mission:
1. Valider ou invalider la décision technique via l'actualité
2. Ajuster le niveau de risque (SL/TP) selon la volatilité fondamentale
3. Servir de GARDE-FOU — si l'actu contredit le technique, dis HOLD

Réponds UNIQUEMENT en JSON:
{{"decision":"BUY|SELL|HOLD","confidence":0.0-1.0,"sl_pips":int,"tp_pips":int,"fundamental_risk":"LOW|MEDIUM|HIGH","news_impact":"max 30 mots","override_technical":true|false}}"""


# ============================================================
# COUCHE TECHNIQUE — Groq principal + fallbacks
# ============================================================

def call_groq(prompt: str) -> Optional[dict]:
    """Appel Groq — modèle le plus rapide et gros quota gratuit"""
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,      # faible température = décisions plus cohérentes
            max_tokens=150,       # on limite strictement — on veut juste le JSON
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        logger.info(f"Groq OK: {result['decision']} (conf: {result['confidence']})")
        return result
    except Exception as e:
        logger.warning(f"Groq échoué: {e}")
        return None


def call_mistral(prompt: str) -> Optional[dict]:
    """Mistral — 1er fallback technique si Groq tombe"""
    try:
        response = mistral_client.chat.completions.create(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=150
        )
        content = response.choices[0].message.content
        # Mistral ne supporte pas toujours response_format, on parse manuellement
        start = content.find('{')
        end = content.rfind('}') + 1
        result = json.loads(content[start:end])
        logger.info(f"Mistral OK: {result['decision']}")
        return result
    except Exception as e:
        logger.warning(f"Mistral échoué: {e}")
        return None


def call_openrouter(prompt: str) -> Optional[dict]:
    """OpenRouter — fallback ultime, accès à plusieurs modèles"""
    try:
        response = openrouter_client.chat.completions.create(
            model="meta-llama/llama-3.1-8b-instruct:free",  # gratuit sur OpenRouter
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=150
        )
        content = response.choices[0].message.content
        start = content.find('{')
        end = content.rfind('}') + 1
        result = json.loads(content[start:end])
        logger.info(f"OpenRouter OK: {result['decision']}")
        return result
    except Exception as e:
        logger.warning(f"OpenRouter échoué: {e}")
        return None


def get_technical_analysis(symbol: str, market_data: dict) -> dict:
    """
    Analyse technique avec cascade de fallbacks.
    Groq → Mistral → OpenRouter → décision par défaut (HOLD)
    Gemini et DeepSeek sont EXCLUS de la technique pour économiser leurs quotas.
    """
    prompt = build_technical_prompt(symbol, market_data)

    # Essai 1 : Groq
    result = call_groq(prompt)
    if result:
        result['source'] = 'groq'
        return result

    # Essai 2 : Mistral
    logger.warning(f"[{symbol}] Groq indisponible, passage à Mistral...")
    result = call_mistral(prompt)
    if result:
        result['source'] = 'mistral'
        return result

    # Essai 3 : OpenRouter
    logger.warning(f"[{symbol}] Mistral indisponible, passage à OpenRouter...")
    result = call_openrouter(prompt)
    if result:
        result['source'] = 'openrouter'
        return result

    # Aucune IA disponible → HOLD par sécurité
    logger.error(f"[{symbol}] Toutes les IAs techniques indisponibles — HOLD forcé")
    return {
        "decision": "HOLD",
        "confidence": 0.0,
        "sl_pips": 30,
        "tp_pips": 60,
        "lot_size": 0.01,
        "reason": "Toutes IAs indisponibles",
        "source": "fallback_safe"
    }


# ============================================================
# COUCHE FONDAMENTALE — Gemini + DeepSeek (Premium/Partner)
# ============================================================

def call_gemini(prompt: str) -> Optional[dict]:
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        content = response.text
        start = content.find('{')
        end = content.rfind('}') + 1
        result = json.loads(content[start:end])
        logger.info(f"Gemini OK: {result['decision']}")
        return result
    except Exception as e:
        logger.warning(f"Gemini échoué: {e}")
        return None


def call_deepseek(prompt: str) -> Optional[dict]:
    """DeepSeek — analyse de sentiment, fallback fondamental"""
    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=200
        )
        content = response.choices[0].message.content
        start = content.find('{')
        end = content.rfind('}') + 1
        result = json.loads(content[start:end])
        logger.info(f"DeepSeek OK: {result['decision']}")
        return result
    except Exception as e:
        logger.warning(f"DeepSeek échoué: {e}")
        return None


def get_fundamental_analysis(symbol: str, technical_result: dict) -> dict:
    """
    Analyse fondamentale — uniquement pour Premium et Partner.
    Gemini en principal (accès web), DeepSeek en fallback.
    Si les deux tombent → on retourne le résultat technique tel quel
    mais avec un flag pour signaler l'absence de garde-fou fondamental.
    """
    prompt = build_fundamental_prompt(symbol, technical_result)

    # Essai 1 : Gemini (accès web = meilleure analyse fondamentale)
    result = call_gemini(prompt)
    if result:
        result['source'] = 'gemini'
        return result

    # Essai 2 : DeepSeek
    logger.warning(f"[{symbol}] Gemini indisponible, passage à DeepSeek...")
    result = call_deepseek(prompt)
    if result:
        result['source'] = 'deepseek'
        return result

    # Aucune IA fondamentale → on garde la décision technique mais on réduit le risque
    logger.warning(f"[{symbol}] Aucune IA fondamentale — risque réduit par précaution")
    return {
        "decision": technical_result['decision'],
        "confidence": technical_result['confidence'] * 0.7,  # réduit la confiance
        "sl_pips": int(technical_result['sl_pips'] * 0.8),   # SL plus serré = moins risqué
        "tp_pips": technical_result['tp_pips'],
        "fundamental_risk": "MEDIUM",
        "news_impact": "Analyse fondamentale indisponible",
        "override_technical": False,
        "source": "fallback_technical_only"
    }


# ============================================================
# MOTEUR DE DÉCISION FINAL — Fusion technique + fondamentale
# ============================================================

def make_trading_decision(
    symbol: str,
    market_data: dict,
    subscription_type: str
) -> dict:
    """
    Fonction principale appelée par le bot pour chaque symbole.
    Retourne les paramètres complets du trade à prendre.

    subscription_type: "basic", "premium", "partner"
    """

    logger.info(f"[{symbol}] Analyse démarrée (plan: {subscription_type})")

    # ── ÉTAPE 1 : Analyse technique (tous les abonnements) ──
    technical = get_technical_analysis(symbol, market_data)

    # ── ÉTAPE 2 : Basic → décision technique pure ──
    if subscription_type == "basic":
        return {
            "symbol": symbol,
            "decision": technical['decision'],
            "confidence": technical['confidence'],
            "sl_pips": technical['sl_pips'],
            "tp_pips": technical['tp_pips'],
            "lot_size": technical['lot_size'],
            "analysis_type": "technical_only",
            "source": technical['source'],
            "reason": technical.get('reason', ''),
        }

    # ── ÉTAPE 3 : Premium/Partner → analyse fondamentale en plus ──
    fundamental = get_fundamental_analysis(symbol, technical)

    # ── ÉTAPE 4 : Garde-fou fondamental ──
    # Si Gemini/DeepSeek dit HOLD → on override TOUJOURS la technique
    if fundamental.get('override_technical') and fundamental['decision'] == 'HOLD':
        logger.info(f"[{symbol}] HOLD forcé par l'analyse fondamentale")
        return {
            "symbol": symbol,
            "decision": "HOLD",
            "confidence": fundamental['confidence'],
            "sl_pips": 0,
            "tp_pips": 0,
            "lot_size": 0,
            "analysis_type": "fundamental_override",
            "source": fundamental['source'],
            "reason": f"Fondamentale bloque: {fundamental.get('news_impact', '')}",
            "fundamental_risk": fundamental.get('fundamental_risk', 'HIGH'),
        }

    # ── ÉTAPE 5 : Fusion des paramètres (moyenne pondérée) ──
    # Partner : Gemini pèse plus (60%) / Technique (40%)
    # Premium : 50/50
    if subscription_type == "partner":
        w_tech, w_fund = 0.4, 0.6
    else:  # premium
        w_tech, w_fund = 0.5, 0.5

    # Si les deux IAs sont en désaccord sur la direction → HOLD par prudence
    if technical['decision'] != fundamental['decision']:
        if technical['decision'] != 'HOLD' and fundamental['decision'] != 'HOLD':
            logger.info(f"[{symbol}] Désaccord BUY/SELL entre IAs → HOLD")
            return {
                "symbol": symbol,
                "decision": "HOLD",
                "confidence": 0.3,
                "sl_pips": 0,
                "tp_pips": 0,
                "lot_size": 0,
                "analysis_type": "disagreement_hold",
                "source": f"{technical['source']}+{fundamental['source']}",
                "reason": "Désaccord technique/fondamental",
            }

    # Les deux s'accordent → on fusionne les paramètres
    final_decision = technical['decision'] if technical['decision'] != 'HOLD' else fundamental['decision']

    # Ajustement du SL selon le risque fondamental
    risk_multiplier = {
        "LOW": 1.2,     # risque faible → SL plus large, on laisse respirer
        "MEDIUM": 1.0,  # risque normal
        "HIGH": 0.7     # risque élevé → SL serré, on protège le capital
    }.get(fundamental.get('fundamental_risk', 'MEDIUM'), 1.0)

    final_sl = int(
        technical['sl_pips'] * w_tech +
        fundamental['sl_pips'] * w_fund
    ) * risk_multiplier

    final_tp = int(
        technical['tp_pips'] * w_tech +
        fundamental['tp_pips'] * w_fund
    )

    final_confidence = (
        technical['confidence'] * w_tech +
        fundamental['confidence'] * w_fund
    )

    # Lot size proportionnel à la confiance (plus on est sûr, plus on met)
    # Plafonné selon l'abonnement
    max_lot = {"basic": 0.1, "premium": 0.5, "partner": 1.0}[subscription_type]
    final_lot = round(min(technical['lot_size'] * final_confidence, max_lot), 2)

    return {
        "symbol": symbol,
        "decision": final_decision,
        "confidence": round(final_confidence, 2),
        "sl_pips": int(final_sl),
        "tp_pips": final_tp,
        "lot_size": final_lot,
        "fundamental_risk": fundamental.get('fundamental_risk', 'MEDIUM'),
        "analysis_type": f"combined_{subscription_type}",
        "source": f"{technical['source']}+{fundamental['source']}",
        "reason": fundamental.get('news_impact', technical.get('reason', '')),
    }