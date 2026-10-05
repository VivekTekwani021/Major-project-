"""
BharatRoad Twin - Simulation Runner Service
=============================================
Runs SUMO traffic simulations with baseline vs realistic scenarios.
Uses TraCI to control SUMO programmatically.
Falls back to demo data when SUMO is not available.
"""

from datetime import datetime
from typing import Optional
from loguru import logger
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks

from app.config import settings, get_simulation_params, DEMO_DIR, DATA_DIR
from app.models import SimulationRun, ConditionScore
from app.schemas import SimulationRequest
from app.utils import load_json


class SimulationRunnerService:
    """
    Runs traffic simulations using SUMO (or demo data fallback).
    
    Two scenarios:
    1. BASELINE: Ideal road conditions, uniform speeds/widths
    2. REALISTIC: Condition-aware speeds, heterogeneous traffic with sublane model
    """

    def __init__(self, db: Session):
        self.db = db
        self.params = get_simulation_params()

    def run(self, request: SimulationRequest, background_tasks: BackgroundTasks) -> dict:
        """
        Start simulation(s) for the requested network.
        If SUMO is available, runs actual simulation as background task.
        Otherwise, loads demo results immediately.
        """
        # Get vehicle mix
        vehicle_mix = request.vehicle_mix
        if vehicle_mix is None:
            mix_config = self.params.get("vehicle_mix", {})
            vehicle_mix_dict = mix_config
        else:
            vehicle_mix_dict = vehicle_mix.model_dump()

        results = {"network_id": request.network_id, "runs": []}

        if settings.sumo_available and not settings.demo_mode:
            # Run actual SUMO simulation (background task)
            if request.run_baseline:
                baseline_run = self._create_run(
                    request.network_id, "baseline", vehicle_mix_dict,
                    request.total_trips, request.random_seed, request.simulation_time,
                )
                background_tasks.add_task(
                    self._execute_sumo, baseline_run.id, "baseline"
                )
                results["runs"].append({
                    "id": baseline_run.id,
                    "scenario": "baseline",
                    "status": "pending",
                })

            if request.run_realistic:
                realistic_run = self._create_run(
                    request.network_id, "realistic", vehicle_mix_dict,
                    request.total_trips, request.random_seed, request.simulation_time,
                )
                background_tasks.add_task(
                    self._execute_sumo, realistic_run.id, "realistic"
                )
                results["runs"].append({
                    "id": realistic_run.id,
                    "scenario": "realistic",
                    "status": "pending",
                })

            results["message"] = "Simulations started as background tasks. Poll status endpoint for progress."
        else:
            # Load demo results
            results = self._load_demo_results(request.network_id, vehicle_mix_dict)

        return results

    def _create_run(
        self,
        network_id: int,
        scenario: str,
        vehicle_mix: dict,
        total_trips: int,
        random_seed: int,
        simulation_time: int,
    ) -> SimulationRun:
        """Create a SimulationRun record in the database."""
        run = SimulationRun(
            network_id=network_id,
            scenario=scenario,
            vehicle_mix=vehicle_mix,
            total_trips=total_trips,
            random_seed=random_seed,
            simulation_time=simulation_time,
            status="pending",
            source="sumo",
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def _execute_sumo(self, run_id: int, scenario: str):
        """
        Execute a SUMO simulation (called as a background task).
        This would use TraCI to control SUMO. Implementation deferred to Phase 2.
        """
        logger.info(f"SUMO simulation started: run_id={run_id}, scenario={scenario}")
        # Full TraCI implementation in Phase 2
        pass

    def _load_demo_results(self, network_id: int, vehicle_mix: dict) -> dict:
        """
        Load pre-computed demo simulation results.
        Creates database records marked as demo data.
        """
        logger.info(f"Loading demo simulation results for network {network_id}")

        demo_path = DEMO_DIR / "demo_simulation_results.json"
        if not demo_path.exists():
            raise FileNotFoundError("Demo simulation results not found")

        demo_data = load_json(demo_path)
        results = {"network_id": network_id, "runs": [], "is_demo": True}

        for scenario_key in ["baseline", "realistic"]:
            scenario_data = demo_data.get(scenario_key)
            if not scenario_data:
                continue

            # Create database record
            run = SimulationRun(
                network_id=network_id,
                scenario=scenario_key,
                vehicle_mix=vehicle_mix,
                total_trips=500,
                random_seed=42,
                simulation_time=3600,
                status="completed",
                is_demo=True,
                source="demo",
                avg_travel_time=scenario_data.get("avg_travel_time"),
                avg_speed=scenario_data.get("avg_speed"),
                avg_delay=scenario_data.get("avg_delay"),
                total_vehicles_completed=scenario_data.get("total_vehicles_completed"),
                throughput=scenario_data.get("throughput"),
                edge_results=scenario_data.get("edge_results"),
                completed_at=datetime.utcnow(),
            )
            self.db.add(run)
            self.db.commit()
            self.db.refresh(run)

            results["runs"].append({
                "id": run.id,
                "scenario": scenario_key,
                "status": "completed",
                "is_demo": True,
                "avg_travel_time": run.avg_travel_time,
                "avg_speed": run.avg_speed,
                "avg_delay": run.avg_delay,
                "throughput": run.throughput,
            })

        results["message"] = (
            "Demo results loaded. These are SYNTHETIC PLACEHOLDER values, "
            "not from actual SUMO simulation. Install SUMO and set DEMO_MODE=false "
            "for real simulations."
        )
        return results
