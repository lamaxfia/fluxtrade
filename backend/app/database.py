# Version Supabase (pour le deployment en ligne)
"""
# SQLAlchemy est le pont entre Python et la base de données
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# On importe notre configuration (qui contient l'URL de la DB)
from app.config import settings

# create_engine = ouvre la "porte" vers la base de données
engine = create_engine(settings.database_url)

# SessionLocal = un "stylo" pour écrire dans la base de données
# autocommit=False : on valide manuellement les changements (plus sûr)
# autoflush=False  : on contrôle quand les données sont envoyées
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = la classe mère dont tous nos "modèles" (tables) vont hériter
Base = declarative_base()

# Cette fonction est un "générateur" — elle ouvre une session,
# la donne à l'appelant, puis la ferme proprement à la fin (même en cas d'erreur)
def get_db():
    db = SessionLocal()
    try:
        yield db        # yield = "tiens, voilà ta session"
    finally:
        db.close()      # always executed — ferme la connexion
"""

# Version SQLite (pour tests locaux)
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# La seule différence avec avant : le connect_args
# SQLite n'accepte pas les accès depuis plusieurs threads par défaut
# check_same_thread=False désactive cette restriction (nécessaire pour FastAPI)
# On l'applique uniquement si l'URL contient "sqlite", sinon on laisse vide
connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}

engine = create_engine(settings.database_url, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()