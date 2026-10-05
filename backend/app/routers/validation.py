"""
BharatRoad Twin - Validation Router
=====================================
Endpoints for comparing simulated vs observed travel times.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from loguru import logger

from app.database import get_db
from app.schemas import ValidationRequest, ValidationResponse

router = APIRouter()


@router.post("/run", response_model=ValidationResponse)
async def run_validation(request: ValidationRequest, db: Session = Depends(get_db)):
    """
    Run validation: compare simulated travel times against observed data.
    
    Computes MAPE and RMSE for both baseline and realistic scenarios,
    and reports the improvement percentage.
    
    The observed_travel_times in the request should contain real measurements.
    If using placeholder data, results will be marked as placeholders.
    """
    from app.services.validation_engine import ValidationEngineService
    
    try:
        engine = ValidationEngineService(db)
        result = engine.validate(request)
        return result
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{validation_id}", response_model=ValidationResponse)
async def get_validation_result(validation_id: int, db: Session = Depends(get_db)):
    """Retrieve a previous validation result."""
    from app.models import ValidationResult
    
    result = db.query(ValidationResult).filter(ValidationResult.id == validation_id).first()
    if not result:
        raise HTTPException(status_code=404, detail=f"Validation {validation_id} not found")
    
    return ValidationResponse(
        id=result.id,
        baseline_mape=result.baseline_mape,
        realistic_mape=result.realistic_mape,
        baseline_rmse=result.baseline_rmse,
        realistic_rmse=result.realistic_rmse,
        improvement_pct=result.improvement_pct,
        comparison_data=result.comparison_data,
        is_placeholder=result.is_placeholder,
        created_at=result.created_at,
    )
