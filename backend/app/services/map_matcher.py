"""
BharatRoad Twin - Map Matcher Service
======================================
Matches GPS-located detections to the nearest road edge.

Uses a simple nearest-edge algorithm with a distance threshold:
1. For each detection (lat, lon), find the closest edge in the network.
2. If the distance is within the threshold, assign the detection to that edge.
3. Otherwise, mark it as unmatched.
"""

import math
from typing import Optional
from loguru import logger

from app.utils import haversine_distance


class MapMatcherService:
    """
    Matches point locations (detections) to road network edges.
    
    Uses a brute-force nearest-edge approach which is fine for
    small-to-medium networks (< 5000 edges). For larger networks,
    consider using an R-tree spatial index.
    """

    def __init__(self, max_distance_m: float = 50.0):
        """
        Args:
            max_distance_m: Maximum distance (meters) to consider a match valid.
                            Detections farther than this from any edge are unmatched.
        """
        self.max_distance_m = max_distance_m

    def match_detection(
        self,
        lat: float,
        lon: float,
        edges: list[dict],
    ) -> tuple[Optional[str], Optional[float]]:
        """
        Find the nearest edge to a point.
        
        Args:
            lat: Detection latitude
            lon: Detection longitude
            edges: List of edge dicts, each with 'edge_id' and 'coordinates'
                   where coordinates is a list of [lon, lat] pairs.
        
        Returns:
            (edge_id, distance_m) or (None, None) if no match within threshold.
        """
        best_edge_id = None
        best_distance = float("inf")

        for edge in edges:
            edge_id = edge.get("edge_id", "")
            coords = edge.get("coordinates", [])
            
            if len(coords) < 2:
                continue

            # Find minimum distance from point to any segment of this edge
            min_dist = self._point_to_polyline_distance(lat, lon, coords)
            
            if min_dist < best_distance:
                best_distance = min_dist
                best_edge_id = edge_id

        if best_distance <= self.max_distance_m:
            return best_edge_id, round(best_distance, 2)
        
        return None, None

    def match_detections_batch(
        self,
        detections: list[dict],
        edges: list[dict],
    ) -> list[dict]:
        """
        Match a batch of detections to edges.
        
        Args:
            detections: List of dicts with 'latitude' and 'longitude'
            edges: List of edge dicts with 'edge_id' and 'coordinates'
        
        Returns:
            List of dicts with added 'matched_edge_id' and 'match_distance_m'
        """
        matched = 0
        total = len(detections)
        
        for det in detections:
            edge_id, distance = self.match_detection(
                det["latitude"], det["longitude"], edges
            )
            det["matched_edge_id"] = edge_id
            det["match_distance_m"] = distance
            if edge_id:
                matched += 1

        logger.info(f"Map matching: {matched}/{total} detections matched to edges")
        return detections

    def _point_to_polyline_distance(
        self,
        lat: float,
        lon: float,
        coords: list[list[float]],
    ) -> float:
        """
        Calculate the minimum distance from a point to a polyline.
        coords is a list of [lon, lat] pairs (GeoJSON order).
        
        Uses perpendicular distance to each segment.
        """
        min_dist = float("inf")

        for i in range(len(coords) - 1):
            # Segment endpoints (convert from [lon, lat] to [lat, lon])
            seg_lat1, seg_lon1 = coords[i][1], coords[i][0]
            seg_lat2, seg_lon2 = coords[i + 1][1], coords[i + 1][0]
            
            dist = self._point_to_segment_distance(
                lat, lon, seg_lat1, seg_lon1, seg_lat2, seg_lon2
            )
            min_dist = min(min_dist, dist)

        return min_dist

    def _point_to_segment_distance(
        self,
        plat: float, plon: float,
        slat1: float, slon1: float,
        slat2: float, slon2: float,
    ) -> float:
        """
        Calculate the perpendicular distance from a point to a line segment.
        All coordinates in decimal degrees. Returns distance in meters.
        
        Uses the projection formula to find the closest point on the segment,
        then computes haversine distance to that point.
        """
        # Convert to simple x,y for projection (approximate)
        # This works well for small areas (within a city)
        cos_lat = math.cos(math.radians(plat))
        
        # Point relative to segment start
        dx = (plon - slon1) * cos_lat
        dy = plat - slat1
        
        # Segment vector
        sx = (slon2 - slon1) * cos_lat
        sy = slat2 - slat1
        
        # Segment length squared
        seg_len_sq = sx * sx + sy * sy
        
        if seg_len_sq < 1e-12:
            # Degenerate segment (start == end)
            return haversine_distance(plat, plon, slat1, slon1)
        
        # Projection parameter (0 = at start, 1 = at end)
        t = max(0.0, min(1.0, (dx * sx + dy * sy) / seg_len_sq))
        
        # Closest point on segment
        closest_lon = slon1 + t * (slon2 - slon1)
        closest_lat = slat1 + t * (slat2 - slat1)
        
        return haversine_distance(plat, plon, closest_lat, closest_lon)
