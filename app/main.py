import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config import settings
from app.database import init_db
from app.routers import token_router, call_router, lead_router, booking_router
from app.routers.whatsapp_router import router as whatsapp_router
from app.routers.campaign_router import router as campaign_router
from app.routers.auth_router import router as auth_router
from fastapi.staticfiles import StaticFiles
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("voice-agent-main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing SQLite/MySQL Database schema...")
    await init_db()
    logger.info("🚀 LiveKit WebRTC Voice Agent Platform is ready!")
    yield
    logger.info("Shutting down Voice Agent Server.")

app = FastAPI(
    title="AI Voice Calling Agent (LiveKit WebRTC + Python)",
    description="Ultra-low latency real-time voice calling platform powered by LiveKit WebRTC, Silero VAD, Sarvam AI, and ElevenLabs.",
    version="2.1.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core Routers
app.include_router(auth_router)
app.include_router(token_router)
app.include_router(call_router)
app.include_router(lead_router)
app.include_router(booking_router)
app.include_router(whatsapp_router)
app.include_router(campaign_router)

# Mount React frontend static files
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ui_dist_path = os.path.join(project_root, "ui", "dist")
ui_static_path = ui_dist_path if os.path.exists(ui_dist_path) else os.path.join(project_root, "ui")

if os.path.exists(ui_static_path):
    app.mount("/", StaticFiles(directory=ui_static_path, html=True), name="ui")

@app.get("/health")
async def health_check():
    return {
        "status": "UP",
        "service": "voice-agent-python-livekit",
        "transport": "WebRTC (UDP / Opus)",
        "livekit_url": settings.LIVEKIT_URL,
        "environment": settings.ENV
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
