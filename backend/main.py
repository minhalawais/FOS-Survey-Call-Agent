"""
FOS Survey Agent - Backend Main
FastAPI application with LiveKit integration.
"""

import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from loguru import logger

from app.api.routes import router as api_router
from app.api.livekit_routes import router as livekit_router
from app.database import init_db, db

# Load environment
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("=" * 60)
    logger.info("FOS Survey Agent - LiveKit Stack")
    logger.info("=" * 60)
    
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database init failed: {e}")
        raise
    
    logger.info(f"Server: http://0.0.0.0:{os.getenv('PORT', 8000)}")
    logger.info(f"Voice UI: http://0.0.0.0:{os.getenv('PORT', 8000)}/voice")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")


# Create app
app = FastAPI(
    title="FOS Survey Agent",
    description="Production Urdu Voice Survey Agent with LiveKit",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(api_router, prefix="/api")
app.include_router(livekit_router, prefix="/livekit")

# Static files
web_dir = Path(__file__).parent.parent / "web"
if web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "FOS Survey Agent",
        "version": "2.0.0",
        "stack": "LiveKit + Whisper + Qwen + Indic Parler-TTS"
    }


@app.get("/voice")
async def voice_ui():
    """Serve voice UI."""
    voice_file = web_dir / "voice_livekit.html"
    if voice_file.exists():
        return FileResponse(voice_file)
    return {"error": "Voice UI not found"}


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
