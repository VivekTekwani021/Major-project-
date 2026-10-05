"""
BharatRoad Twin - Network Router
==================================
Endpoints for building and retrieving road networks.
Full implementation in Phase 1.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from loguru import logger

from app.database import get_db
from app.schemas import NetworkBuildRequest, NetworkResponse
from app.config import settings, get_corridors, DEMO_DIR
from app.utils import load_json

router = APIRouter()


@router.post("/build", response_model=NetworkResponse)
async def build_network(request: NetworkBuildRequest, db: Session = Depends(get_db)):
    """
    Build a road network from OpenStreetMap data.
    
    Provide either:
    - A bounding box (south, west, north, east)
    - A corridor_name from the predefined corridors config
    
    Returns the built network with GeoJSON and quality report.
    """
    from app.services.network_builder import NetworkBuilderService
    
    try:
        builder = NetworkBuilderService(db)
        network = builder.build(request)
        return network
    except Exception as e:
        logger.error(f"Network build failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{network_id}", response_model=NetworkResponse)
async def get_network(network_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a previously built network by ID.
    Includes GeoJSON data and quality report.
    """
    from app.models import Network
    
    network = db.query(Network).filter(Network.id == network_id).first()
    if not network:
        raise HTTPException(status_code=404, detail=f"Network {network_id} not found")
    
    # Load GeoJSON if available
    geojson = None
    if network.geojson_file:
        from pathlib import Path
        geojson_path = Path(network.geojson_file)
        if geojson_path.exists():
            geojson = load_json(geojson_path)
    
    return NetworkResponse(
        id=network.id,
        name=network.name,
        bbox={
            "south": network.bbox_south,
            "west": network.bbox_west,
            "north": network.bbox_north,
            "east": network.bbox_east,
        },
        num_nodes=network.num_nodes,
        num_edges=network.num_edges,
        total_length_km=network.total_length_km,
        quality_report=network.quality_report,
        geojson=geojson,
        created_at=network.created_at,
    )


@router.get("/corridors/list")
async def list_corridors():
    """List all predefined study corridors."""
    corridors_config = get_corridors()
    return {
        "default": corridors_config.get("default_corridor", "ab_road"),
        "corridors": corridors_config.get("corridors", {}),
        "max_area_sq_km": corridors_config.get("max_area_sq_km", 4.0),
    }
