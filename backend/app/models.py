"""
BharatRoad Twin - Database Models
=================================
SQLAlchemy ORM models for storing road networks, 
condition detections, simulation results, and validation data.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text,
    DateTime, JSON, ForeignKey
)
from sqlalchemy.orm import relationship
from app.database import Base


class Network(Base):
    """
    A road network built from OpenStreetMap data.
    Each network represents one bounding box / study area.
    """
    __tablename__ = "networks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    
    # Bounding box (south, west, north, east)
    bbox_south = Column(Float, nullable=False)
    bbox_west = Column(Float, nullable=False)
    bbox_north = Column(Float, nullable=False)
    bbox_east = Column(Float, nullable=False)
    
    # File paths (relative to data directory)
    net_file = Column(String(500), nullable=True)       # SUMO .net.xml path
    geojson_file = Column(String(500), nullable=True)   # GeoJSON of edges
    
    # Statistics
    num_nodes = Column(Integer, default=0)
    num_edges = Column(Integer, default=0)
    total_length_km = Column(Float, default=0.0)
    
    # Data quality report (JSON)
    quality_report = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    condition_scores = relationship("ConditionScore", back_populates="network")
    simulations = relationship("SimulationRun", back_populates="network")

    def __repr__(self):
        return f"<Network id={self.id} name='{self.name}'>"


class ConditionScore(Base):
    """
    Road condition score for a single edge in the network.
    Computed from detected road damage (potholes, cracks, etc.).
    """
    __tablename__ = "condition_scores"

    id = Column(Integer, primary_key=True, index=True)
    network_id = Column(Integer, ForeignKey("networks.id"), nullable=False)
    
    # Edge identification
    edge_id = Column(String(200), nullable=False)     # SUMO edge ID
    
    # Condition score (0 = perfect, 100 = worst)
    score = Column(Float, nullable=False, default=0.0)
    
    # Damage counts by type
    damage_counts = Column(JSON, nullable=True)  # {"D00": 2, "D40": 5, ...}
    
    # Derived penalties
    speed_penalty = Column(Float, default=1.0)     # Multiplier (0.3 to 1.0)
    width_penalty = Column(Float, default=1.0)     # Multiplier (0.5 to 1.0)
    
    # Source: "detection" (from ML) or "demo" (synthetic data)
    source = Column(String(50), default="demo")
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    network = relationship("Network", back_populates="condition_scores")

    def __repr__(self):
        return f"<ConditionScore edge={self.edge_id} score={self.score}>"


class Detection(Base):
    """
    A single road damage detection from video inference.
    Stores only class/confidence/location — no image data.
    """
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True)
    network_id = Column(Integer, ForeignKey("networks.id"), nullable=True)
    
    # Detection info
    damage_class = Column(String(10), nullable=False)  # D00, D10, D20, D40, etc.
    confidence = Column(Float, nullable=False)
    
    # Location (GPS coordinates)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Bounding box in frame (for reference)
    bbox_x1 = Column(Float, nullable=True)
    bbox_y1 = Column(Float, nullable=True)
    bbox_x2 = Column(Float, nullable=True)
    bbox_y2 = Column(Float, nullable=True)
    
    # Frame info
    frame_number = Column(Integer, nullable=True)
    timestamp = Column(DateTime, nullable=True)
    
    # Map matching result
    matched_edge_id = Column(String(200), nullable=True)
    match_distance_m = Column(Float, nullable=True)
    
    source = Column(String(50), default="demo")
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Detection {self.damage_class} conf={self.confidence:.2f}>"


class SimulationRun(Base):
    """
    A single simulation run (either BASELINE or REALISTIC scenario).
    """
    __tablename__ = "simulation_runs"

    id = Column(Integer, primary_key=True, index=True)
    network_id = Column(Integer, ForeignKey("networks.id"), nullable=False)
    
    # Scenario type
    scenario = Column(String(20), nullable=False)  # "baseline" or "realistic"
    
    # Parameters used
    vehicle_mix = Column(JSON, nullable=True)
    total_trips = Column(Integer, default=500)
    random_seed = Column(Integer, default=42)
    simulation_time = Column(Integer, default=3600)
    
    # Status: "pending", "running", "completed", "failed", "demo"
    status = Column(String(20), default="pending")
    progress = Column(Float, default=0.0)  # 0 to 100
    error_message = Column(Text, nullable=True)
    
    # Aggregate results
    avg_travel_time = Column(Float, nullable=True)
    avg_speed = Column(Float, nullable=True)
    avg_delay = Column(Float, nullable=True)
    total_vehicles_completed = Column(Integer, nullable=True)
    throughput = Column(Float, nullable=True)  # vehicles per hour
    
    # Detailed results (JSON)
    edge_results = Column(JSON, nullable=True)     # Per-edge metrics
    route_results = Column(JSON, nullable=True)    # Selected route metrics
    
    # Is this demo data?
    is_demo = Column(Boolean, default=False)
    
    # Source: "sumo" or "demo"
    source = Column(String(50), default="demo")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    network = relationship("Network", back_populates="simulations")

    def __repr__(self):
        return f"<SimulationRun id={self.id} scenario='{self.scenario}' status='{self.status}'>"


class ValidationResult(Base):
    """
    Stores validation/calibration results comparing 
    simulated vs observed travel times.
    """
    __tablename__ = "validation_results"

    id = Column(Integer, primary_key=True, index=True)
    network_id = Column(Integer, ForeignKey("networks.id"), nullable=True)
    
    # Which simulation runs are being compared
    baseline_run_id = Column(Integer, ForeignKey("simulation_runs.id"), nullable=True)
    realistic_run_id = Column(Integer, ForeignKey("simulation_runs.id"), nullable=True)
    
    # Error metrics
    baseline_mape = Column(Float, nullable=True)    # Mean Absolute Percentage Error
    realistic_mape = Column(Float, nullable=True)
    baseline_rmse = Column(Float, nullable=True)    # Root Mean Square Error
    realistic_rmse = Column(Float, nullable=True)
    improvement_pct = Column(Float, nullable=True)  # How much better is realistic?
    
    # Detailed comparison data (JSON)
    comparison_data = Column(JSON, nullable=True)
    
    # Calibration results (JSON)
    calibration_results = Column(JSON, nullable=True)
    
    # Is this from placeholder/demo data?
    is_placeholder = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ValidationResult baseline_mape={self.baseline_mape} realistic_mape={self.realistic_mape}>"
