# On importe BaseSettings de pydantic — c'est un outil qui lit
# automatiquement les variables de ton fichier .env
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Ces variables seront remplies automatiquement depuis .env
    database_url: str
    secret_key: str
    access_token_expire_minutes: int = 1440  # valeur par défaut : 24h
    stripe_secret_key: str
    stripe_webhook_secret: str = ""
    groq_api_key: str = ""
    gemini_api_key: str = ""
    deepseek_api_key: str = ""
    mistral_api_key: str = ""
    openrouter_api_key: str = ""
    metaapi_token: str = ""
    # Ajoute ici :
    paypal_client_id: str = ""
    paypal_client_secret: str = ""
    paypal_mode: str = "sandbox"
    cinetpay_api_key: str = ""
    cinetpay_site_id: str = ""
    
    # Dis à pydantic où trouver le fichier .env
    class Config:
        env_file = ".env"

# On crée UNE instance de Settings, réutilisable partout dans le projet
settings = Settings()