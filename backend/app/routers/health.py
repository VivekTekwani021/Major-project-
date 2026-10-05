"""
BharatRoad Twin - Health Check Router
======================================
Simple health check endpoint.
"""

from fastapi import APIRouter
from app.config import settings
from app.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check if the API is running and report system capabilities.
    Returns SUMO availability, demo mode status, etc.
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        sumo_available=settings.sumo_available,
        demo_mode=settings.demo_mode,
        database="connected",
    )
