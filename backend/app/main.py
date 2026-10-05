"""
BharatRoad Twin - FastAPI Main Application
===========================================
Entry point for the backend API server.
Sets up CORS, routers, database, and middleware.

Run with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings, PROJECT_ROOT
from app.database import init_db


# ── Startup / Shutdown ─────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on startup and shutdown.
    - Creates database tables on startup.
    - Logs configuration summary.
    """
    logger.info("=" * 50)
    logger.info("BharatRoad Twin - Starting Up")
    logger.info("=" * 50)
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Demo Mode: {settings.demo_mode}")
    logger.info(f"SUMO Available: {settings.sumo_available}")
    logger.info(f"Database: {settings.database_url}")
    
    # Create database tables
    init_db()
    logger.info("Database initialized.")
    
    yield  # App is running
    
    logger.info("BharatRoad Twin - Shutting Down")


# ── Create FastAPI App ─────────────────────────────────────
app = FastAPI(
    title="BharatRoad Twin API",
    description=(
        "API for accelerating high-fidelity road network modeling "
        "for Indian traffic simulations. Builds road networks from OSM, "
        "detects road conditions with ML, and runs realistic traffic simulations."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── CORS Middleware ────────────────────────────────────────
# Allow the React frontend to make requests to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Import and Include Routers ──────────────────────────────
# Each router handles a specific module of the API.
# We import them here to keep main.py clean.
from app.routers import health, network, condition, simulation, validation

app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(network.router, prefix="/api/network", tags=["Network"])
app.include_router(condition.router, prefix="/api/condition", tags=["Condition"])
app.include_router(simulation.router, prefix="/api/simulation", tags=["Simulation"])
app.include_router(validation.router, prefix="/api/validation", tags=["Validation"])


# ── Root Endpoint ──────────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - welcome message and links."""
    return {
        "message": "BharatRoad Twin API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }
