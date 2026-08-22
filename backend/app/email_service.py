"""
email_service.py — Envoi d'emails via Resend.
"""
import random
import string
import logging
from datetime import datetime, timedelta
import resend
from app.config import settings

logger = logging.getLogger(__name__)

resend.api_key = settings.resend_api_key


def generate_verification_code() -> str:
    """Génère un code à 6 chiffres"""
    return ''.join(random.choices(string.digits, k=6))


def send_verification_email(email: str, username: str, code: str) -> bool:
    """
    Envoie l'email de vérification avec le code.
    Retourne True si succès, False sinon.
    """
    try:
        params = {
            "from": "FluxTrade <onboarding@resend.dev>",
            "to": [email],
            "subject": "Vérifiez votre compte FluxTrade",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0a0a0a; color: #ffffff; padding: 40px; border-radius: 16px;">
                <div style="text-align: center; margin-bottom: 32px;">
                    <h1 style="color: #10b981; font-size: 28px; margin: 0;">
                        Flux<span style="color: #ffffff;">Trade</span>
                    </h1>
                    <p style="color: #6b7280; font-size: 12px; letter-spacing: 2px; margin-top: 4px;">
                        AI-POWERED TRADING PLATFORM
                    </p>
                </div>

                <h2 style="font-size: 22px; margin-bottom: 8px;">Bonjour {username} 👋</h2>
                <p style="color: #9ca3af; margin-bottom: 32px;">
                    Merci de rejoindre FluxTrade ! Entre ce code pour activer ton compte :
                </p>

                <div style="background: #1f2937; border: 2px solid #10b981; border-radius: 12px; padding: 24px; text-align: center; margin-bottom: 32px;">
                    <p style="color: #6b7280; font-size: 12px; letter-spacing: 2px; margin: 0 0 8px 0;">
                        TON CODE DE VÉRIFICATION
                    </p>
                    <p style="font-size: 42px; font-weight: bold; color: #10b981; letter-spacing: 8px; margin: 0;">
                        {code}
                    </p>
                    <p style="color: #6b7280; font-size: 12px; margin: 8px 0 0 0;">
                        Expire dans 15 minutes
                    </p>
                </div>

                <p style="color: #6b7280; font-size: 13px; text-align: center;">
                    Si tu n'es pas à l'origine de cette inscription, ignore cet email.
                </p>
            </div>
            """
        }
        resend.Emails.send(params)
        logger.info(f"Email de vérification envoyé à {email}")
        return True

    except Exception as e:
        logger.error(f"Erreur envoi email à {email}: {e}")
        return False


def send_welcome_email(email: str, username: str) -> bool:
    """Email de bienvenue après vérification réussie"""
    try:
        params = {
            "from": "FluxTrade <onboarding@resend.dev>",
            "to": [email],
            "subject": "Bienvenue sur FluxTrade ! 🚀",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0a0a0a; color: #ffffff; padding: 40px; border-radius: 16px;">
                <div style="text-align: center; margin-bottom: 32px;">
                    <h1 style="color: #10b981; font-size: 28px; margin: 0;">
                        Flux<span style="color: #ffffff;">Trade</span>
                    </h1>
                </div>

                <h2 style="font-size: 22px; margin-bottom: 8px;">Bienvenue {username} ! 🎉</h2>
                <p style="color: #9ca3af; margin-bottom: 24px;">
                    Ton compte est maintenant vérifié. Tu peux te connecter et choisir ton abonnement pour activer le trading IA automatique.
                </p>

                <div style="text-align: center;">
                    <a href="{settings.frontend_url}/pricing" 
                       style="background: #10b981; color: #000000; padding: 14px 32px; border-radius: 12px; text-decoration: none; font-weight: bold; font-size: 16px;">
                        Choisir mon abonnement
                    </a>
                </div>
            </div>
            """
        }
        resend.Emails.send(params)
        return True
    except Exception as e:
        logger.error(f"Erreur email bienvenue {email}: {e}")
        return False