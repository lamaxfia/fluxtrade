from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
import stripe

from app import models
from app.database import get_db
from app.config import settings
from app.routers.auth import ALGORITHM
from jose import jwt, JWTError

# Configure Stripe avec notre clé secrète
stripe.api_key = settings.stripe_secret_key

router = APIRouter(prefix="/payments", tags=["Paiements"])

# --- Prix des abonnements en centimes (Stripe travaille en centimes) ---
# 29.99€ = 2999 centimes
PLANS = {
    "basic":   {"price": 2999,  "name": "FluxTrade Basic",   "interval": "month"},
    "premium": {"price": 11999, "name": "FluxTrade Premium",  "interval": "month"},
    "partner": {"price": 29999, "name": "FluxTrade Partner",  "interval": "month"},
}

# --- Schémas ---

class CheckoutRequest(BaseModel):
    """Données pour créer une session de paiement"""
    plan: str  # "basic", "premium", "partner"

# --- Fonction utilitaire : récupère l'utilisateur depuis le token ---

def get_user_from_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Token invalide")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return user

# --- Routes ---

@router.post("/create-checkout")
def create_checkout_session(
    data: CheckoutRequest,
    token: str,
    db: Session = Depends(get_db)
):
    """
    Crée une session de paiement Stripe.
    Stripe héberge la page de paiement — on n'a pas à gérer les données de carte.
    On redirige l'utilisateur vers la page Stripe, il paie, Stripe nous confirme.
    """
    user = get_user_from_token(token, db)

    if data.plan not in PLANS:
        raise HTTPException(status_code=400, detail="Plan invalide")

    plan = PLANS[data.plan]

    try:
        # Crée la session de paiement sur les serveurs Stripe
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {"name": plan["name"]},
                    # Stripe gère le paiement récurrent
                    "recurring": {"interval": plan["interval"]},
                    "unit_amount": plan["price"],
                },
                "quantity": 1,
            }],
            mode="subscription",
            # URLs de redirection après paiement
            success_url="http://localhost:3000/payment/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="http://localhost:3000/payment/cancel",
            # On passe l'email et l'user_id pour identifier l'utilisateur après paiement
            customer_email=user.email,
            metadata={
                "user_id": str(user.id),
                "plan": data.plan
            }
        )
        return {"checkout_url": session.url}

    except stripe.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook Stripe — Stripe appelle cette route automatiquement après un paiement.
    C'est ici qu'on active l'abonnement de l'utilisateur.
    
    Un webhook c'est comme une sonnette : Stripe sonne à notre porte pour dire
    "hé, untel vient de payer !" et on ouvre l'abonnement.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        # Vérifie que la requête vient bien de Stripe (sécurité)
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Payload invalide")
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Signature invalide")

    # Événement : paiement réussi
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = int(session["metadata"]["user_id"])
        plan = session["metadata"]["plan"]

        # Active l'abonnement dans notre base de données
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user:
            user.subscription_type = plan
            user.subscription_end = datetime.utcnow() + timedelta(days=30)
            db.commit()

    # Événement : abonnement annulé
    elif event["type"] == "customer.subscription.deleted":
        customer_email = event["data"]["object"].get("customer_email")
        if customer_email:
            user = db.query(models.User).filter(
                models.User.email == customer_email
            ).first()
            if user:
                user.subscription_type = "none"
                user.subscription_end = None
                db.commit()

    return {"status": "ok"}


@router.get("/my-subscription")
def get_my_subscription(token: str, db: Session = Depends(get_db)):
    """Retourne les infos d'abonnement de l'utilisateur connecté"""
    user = get_user_from_token(token, db)
    return {
        "subscription_type": user.subscription_type,
        "subscription_end": user.subscription_end,
        "is_active": user.subscription_type != "none"
    }