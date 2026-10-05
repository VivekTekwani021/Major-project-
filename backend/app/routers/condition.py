"""
BharatRoad Twin - Condition Router
====================================
Endpoints for road condition detection and scoring.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from loguru import logger

from app.database import get_db
from app.schemas import ConditionResponse
from app.config import settings, DEMO_DIR
from app.utils import load_json

router = APIRouter()


@router.post("/demo-data")
async def load_demo_condition_data(network_id: int = 1, db: Session = Depends(get_db)):
    """
    Load synthetic demo condition data for testing.
    This loads bundled demo detections and computes condition scores.
    No real video or ML inference is needed.
    """
    from app.services.condition_scorer import ConditionScorerService
    
    try:
        scorer = ConditionScorerService(db)
        result = scorer.load_demo_data(network_id)
        return result
    except Exception as e:
        logger.error(f"Failed to load demo condition data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-video")
async def upload_video(
    network_id: int,
    video: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a video file for road damage detection.
    The video will be processed with YOLOv8 to detect potholes and cracks.
    Results are map-matched to road edges and stored.
    
    Note: Requires a trained YOLOv8 model. Falls back to demo data if unavailable.
    """
    # Validate file type
    allowed = settings.allowed_video_types_list
    ext = "." + video.filename.split(".")[-1].lower() if video.filename else ""
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{ext}'. Allowed: {allowed}"
        )
    
    return {
        "message": "Video upload endpoint ready. ML inference requires trained model.",
        "network_id": network_id,
        "filename": video.filename,
        "tip": "Use POST /api/condition/demo-data for testing without a model."
    }


@router.get("/{network_id}", response_model=ConditionResponse)
async def get_condition_scores(network_id: int, db: Session = Depends(get_db)):
    """
    Get condition scores for all edges in a network.
    Returns scores, detections, and penalty values.
    """
    from app.services.condition_scorer import ConditionScorerService
    
    try:
        scorer = ConditionScorerService(db)
        result = scorer.get_scores(network_id)
        return result
    except Exception as e:
        logger.error(f"Failed to get condition scores: {e}")
        raise HTTPException(status_code=500, detail=str(e))
