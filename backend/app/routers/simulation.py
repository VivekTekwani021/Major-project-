"""
BharatRoad Twin - Simulation Router
=====================================
Endpoints for running and retrieving traffic simulations.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from loguru import logger

from app.database import get_db
from app.schemas import (
    SimulationRequest, SimulationStatus, 
    SimulationResultResponse, ComparisonResponse
)

router = APIRouter()


@router.post("/run")
async def run_simulation(
    request: SimulationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Run baseline and/or realistic traffic simulation.
    
    The simulation runs as a background task. Poll the status endpoint
    to check progress, then retrieve results when complete.
    
    If SUMO is not installed, returns demo results automatically.
    """
    from app.services.simulation_runner import SimulationRunnerService
    
    try:
        runner = SimulationRunnerService(db)
        result = runner.run(request, background_tasks)
        return result
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}/status", response_model=SimulationStatus)
async def get_simulation_status(run_id: int, db: Session = Depends(get_db)):
    """Check the status of a running simulation."""
    from app.models import SimulationRun
    
    sim = db.query(SimulationRun).filter(SimulationRun.id == run_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail=f"Simulation run {run_id} not found")
    
    return SimulationStatus(
        id=sim.id,
        scenario=sim.scenario,
        status=sim.status,
        progress=sim.progress or 0.0,
        error_message=sim.error_message,
    )


@router.get("/{run_id}/results", response_model=SimulationResultResponse)
async def get_simulation_results(run_id: int, db: Session = Depends(get_db)):
    """Get detailed results of a completed simulation run."""
    from app.models import SimulationRun
    
    sim = db.query(SimulationRun).filter(SimulationRun.id == run_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail=f"Simulation run {run_id} not found")
    
    if sim.status not in ("completed", "demo"):
        raise HTTPException(
            status_code=400, 
            detail=f"Simulation is not complete yet (status: {sim.status})"
        )
    
    return SimulationResultResponse(
        id=sim.id,
        scenario=sim.scenario,
        status=sim.status,
        is_demo=sim.is_demo,
        avg_travel_time=sim.avg_travel_time,
        avg_speed=sim.avg_speed,
        avg_delay=sim.avg_delay,
        total_vehicles_completed=sim.total_vehicles_completed,
        throughput=sim.throughput,
        edge_results=sim.edge_results,
        route_results=sim.route_results,
        vehicle_mix=sim.vehicle_mix,
        created_at=sim.created_at,
    )


@router.get("/compare/{network_id}", response_model=ComparisonResponse)
async def compare_scenarios(network_id: int, db: Session = Depends(get_db)):
    """
    Get side-by-side comparison of baseline vs realistic simulations.
    Returns metrics for both scenarios plus derived comparison data.
    """
    from app.models import SimulationRun
    
    # Get the most recent completed runs for this network
    baseline = (
        db.query(SimulationRun)
        .filter(SimulationRun.network_id == network_id)
        .filter(SimulationRun.scenario == "baseline")
        .filter(SimulationRun.status.in_(["completed", "demo"]))
        .order_by(SimulationRun.created_at.desc())
        .first()
    )
    
    realistic = (
        db.query(SimulationRun)
        .filter(SimulationRun.network_id == network_id)
        .filter(SimulationRun.scenario == "realistic")
        .filter(SimulationRun.status.in_(["completed", "demo"]))
        .order_by(SimulationRun.created_at.desc())
        .first()
    )
    
    # Build comparison metrics
    comparison = None
    if baseline and realistic:
        bl_tt = baseline.avg_travel_time or 0
        re_tt = realistic.avg_travel_time or 0
        comparison = {
            "travel_time_increase_pct": ((re_tt - bl_tt) / bl_tt * 100) if bl_tt > 0 else 0,
            "speed_decrease_pct": (
                ((baseline.avg_speed or 0) - (realistic.avg_speed or 0)) 
                / (baseline.avg_speed or 1) * 100
            ),
            "throughput_decrease_pct": (
                ((baseline.throughput or 0) - (realistic.throughput or 0))
                / (baseline.throughput or 1) * 100
            ),
        }
    
    def to_result(sim):
        if not sim:
            return None
        return SimulationResultResponse(
            id=sim.id,
            scenario=sim.scenario,
            status=sim.status,
            is_demo=sim.is_demo,
            avg_travel_time=sim.avg_travel_time,
            avg_speed=sim.avg_speed,
            avg_delay=sim.avg_delay,
            total_vehicles_completed=sim.total_vehicles_completed,
            throughput=sim.throughput,
            edge_results=sim.edge_results,
            route_results=sim.route_results,
            vehicle_mix=sim.vehicle_mix,
            created_at=sim.created_at,
        )
    
    return ComparisonResponse(
        network_id=network_id,
        baseline=to_result(baseline),
        realistic=to_result(realistic),
        comparison=comparison,
    )
