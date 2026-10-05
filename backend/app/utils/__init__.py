"""
BharatRoad Twin - Utility Helpers
=================================
Common utility functions used across the backend.
"""

import json
import math
from pathlib import Path
from typing import Union
from loguru import logger


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth.
    
    Args:
        lat1, lon1: Coordinates of point 1 (decimal degrees)
        lat2, lon2: Coordinates of point 2 (decimal degrees)
    
    Returns:
        Distance in meters.
    """
    R = 6371000  # Earth's radius in meters
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def bbox_area_sq_km(south: float, west: float, north: float, east: float) -> float:
    """
    Estimate the area of a bounding box in square kilometers.
    Uses a simple approximation based on haversine distances.
    
    Args:
        south, west, north, east: Bounding box coordinates
    
    Returns:
        Approximate area in square kilometers.
    """
    # Width at the center latitude
    center_lat = (south + north) / 2
    width_m = haversine_distance(center_lat, west, center_lat, east)
    height_m = haversine_distance(south, west, north, west)
    return (width_m * height_m) / 1_000_000


def save_json(data: Union[dict, list], filepath: Path) -> None:
    """Save data as a formatted JSON file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    logger.debug(f"Saved JSON to {filepath}")


def load_json(filepath: Path) -> Union[dict, list]:
    """Load data from a JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value to a range."""
    return max(min_val, min(value, max_val))


def format_seconds(seconds: float) -> str:
    """Format seconds into a human-readable string like '5m 30s'."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}m {secs}s"
