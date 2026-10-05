"""
BharatRoad Twin - Pydantic Schemas
===================================
Request/response schemas for the API.
These define what data comes in and goes out of each endpoint.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# Network Schemas
# ============================================================

class BoundingBox(BaseModel):
    """A geographic bounding box defined by four coordinates."""
    south: float = Field(..., ge=-90, le=90, description="Southern latitude")
    west: float = Field(..., ge=-180, le=180, description="Western longitude")
    north: float = Field(..., ge=-90, le=90, description="Northern latitude")
    east: float = Field(..., ge=-180, le=180, description="Eastern longitude")


class NetworkBuildRequest(BaseModel):
    """Request to build a road network from OpenStreetMap."""
    bbox: Optional[BoundingBox] = None
    corridor_name: Optional[str] = Field(None, description="Predefined corridor name from config")
    name: Optional[str] = Field(None, description="Custom name for this network")


class QualityReport(BaseModel):
    """Data quality report for a built network."""
    total_edges: int
    edges_with_lanes_tag: int
    edges_with_width_tag: int
    edges_with_speed_tag: int
    pct_lanes_estimated: float
    pct_width_estimated: float
    pct_speed_estimated: float
    road_class_distribution: dict


class NetworkResponse(BaseModel):
    """Response after building or retrieving a network."""
    id: int
    name: str
    bbox: BoundingBox
    num_nodes: int
    num_edges: int
    total_length_km: float
    quality_report: Optional[dict] = None
    geojson: Optional[dict] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Condition Schemas
# ============================================================

class DetectionItem(BaseModel):
    """A single road damage detection."""
    damage_class: str
    confidence: float
    latitude: float
    longitude: float
    frame_number: Optional[int] = None
    matched_edge_id: Optional[str] = None
    match_distance_m: Optional[float] = None


class ConditionScoreItem(BaseModel):
    """Condition score for a single edge."""
    edge_id: str
    score: float
    speed_penalty: float
    width_penalty: float
    damage_counts: Optional[dict] = None


class ConditionResponse(BaseModel):
    """Response with condition data for a network."""
    network_id: int
    total_detections: int
    edges_with_damage: int
    avg_score: float
    scores: list[ConditionScoreItem]
    detections: list[DetectionItem]
    source: str  # "detection" or "demo"


# ============================================================
# Simulation Schemas
# ============================================================

class VehicleMix(BaseModel):
    """Vehicle type mix percentages (should sum to 100)."""
    two_wheeler: float = 45.0
    auto_rickshaw: float = 10.0
    car: float = 30.0
    bus: float = 5.0
    bicycle: float = 5.0
    truck: float = 5.0


class SimulationRequest(BaseModel):
    """Request to run a traffic simulation."""
    network_id: int
    vehicle_mix: Optional[VehicleMix] = None
    total_trips: int = Field(500, ge=10, le=5000)
    random_seed: int = Field(42, ge=0)
    simulation_time: int = Field(3600, ge=300, le=7200)
    run_baseline: bool = True
    run_realistic: bool = True


class SimulationStatus(BaseModel):
    """Current status of a simulation run."""
    id: int
    scenario: str
    status: str
    progress: float
    error_message: Optional[str] = None


class SimulationResultResponse(BaseModel):
    """Results from a completed simulation run."""
    id: int
    scenario: str
    status: str
    is_demo: bool
    avg_travel_time: Optional[float] = None
    avg_speed: Optional[float] = None
    avg_delay: Optional[float] = None
    total_vehicles_completed: Optional[int] = None
    throughput: Optional[float] = None
    edge_results: Optional[dict] = None
    route_results: Optional[dict] = None
    vehicle_mix: Optional[dict] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComparisonResponse(BaseModel):
    """Side-by-side comparison of baseline vs realistic."""
    network_id: int
    baseline: Optional[SimulationResultResponse] = None
    realistic: Optional[SimulationResultResponse] = None
    comparison: Optional[dict] = None  # Derived comparison metrics


# ============================================================
# Validation Schemas
# ============================================================

class ObservedTravelTime(BaseModel):
    """A single observed travel time entry."""
    route_name: str
    origin: str
    destination: str
    observed_time_seconds: float
    time_of_day: Optional[str] = "peak"
    is_placeholder: bool = True


class ValidationRequest(BaseModel):
    """Request to run validation against observed data."""
    network_id: int
    baseline_run_id: Optional[int] = None
    realistic_run_id: Optional[int] = None
    observed_travel_times: list[ObservedTravelTime]


class ValidationResponse(BaseModel):
    """Validation results with MAPE and RMSE."""
    id: int
    baseline_mape: Optional[float] = None
    realistic_mape: Optional[float] = None
    baseline_rmse: Optional[float] = None
    realistic_rmse: Optional[float] = None
    improvement_pct: Optional[float] = None
    comparison_data: Optional[dict] = None
    is_placeholder: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# General Schemas
# ============================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    sumo_available: bool
    demo_mode: bool
    database: str


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    error_code: Optional[str] = None
