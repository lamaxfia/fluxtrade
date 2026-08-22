from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth, users, admin, payments, agent_routes
from app.scheduler import start_scheduler
from agent.trading_agent import start_all_active_agents
import logging

# Réduit le bruit des bibliothèques internes MetaApi — on ne veut que NOS logs
logging.getLogger("engineio").setLevel(logging.WARNING)
logging.getLogger("socketio").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FluxTrade API",
    description="API de la plateforme de trading IA FluxTrade",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(payments.router)
app.include_router(agent_routes.router)

@app.on_event("startup")
async def startup_event():
    start_all_active_agents()
    start_scheduler()

@app.get("/")
def root():
    return {"message": "API FluxTrade opérationnelle 🚀"}