"""
BharatRoad Twin - Network Builder Service
==========================================
Builds SUMO-ready road networks from OpenStreetMap data.
Applies Indian-road correction rules (lane widths, speeds, LHT, etc.).

This is the core of Module 1.
"""

import json
import math
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger
from sqlalchemy.orm import Session

from app.config import (
    settings, get_road_rules, get_corridors,
    DATA_DIR, DEMO_DIR, PROJECT_ROOT
)
from app.models import Network
from app.schemas import NetworkBuildRequest, NetworkResponse, BoundingBox
from app.utils import bbox_area_sq_km, save_json, load_json


class NetworkBuilderService:
    """
    Service to build road networks from OpenStreetMap data.
    
    Workflow:
    1. Resolve the bounding box (from corridor name or explicit bbox)
    2. Download OSM data via OSMnx
    3. Apply Indian-road correction rules
    4. Export to SUMO network file (.net.xml)
    5. Export GeoJSON for the frontend map
    6. Generate data quality report
    7. Save everything to the database
    """

    def __init__(self, db: Session):
        self.db = db
        self.rules = get_road_rules()
        self.road_defaults = self.rules.get("road_defaults", {})
        self.cleaning = self.rules.get("cleaning", {})

    def build(self, request: NetworkBuildRequest) -> NetworkResponse:
        """
        Build a network from a bounding box or corridor name.
        
        Returns a NetworkResponse with GeoJSON, stats, and quality report.
        """
        # Step 1: Resolve bounding box
        bbox, name = self._resolve_bbox(request)
        logger.info(f"Building network '{name}' for bbox: {bbox}")

        # Step 2: Check area limit
        area = bbox_area_sq_km(bbox.south, bbox.west, bbox.north, bbox.east)
        max_area = get_corridors().get("max_area_sq_km", 4.0)
        if area > max_area:
            raise ValueError(
                f"Area {area:.2f} km² exceeds maximum {max_area} km². "
                f"Please use a smaller bounding box."
            )

        # Step 3: Download and process OSM data
        try:
            import osmnx as ox
            graph, quality_report, edges_data = self._build_from_osm(bbox)
        except ImportError:
            logger.warning("OSMnx not available, using demo data")
            return self._load_demo_network(bbox, name)
        except Exception as e:
            logger.warning(f"OSM download failed ({e}), falling back to demo data")
            return self._load_demo_network(bbox, name)

        # Step 4: Save files
        network_dir = DATA_DIR / "networks" / f"net_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        network_dir.mkdir(parents=True, exist_ok=True)

        geojson_path = network_dir / "edges.geojson"
        save_json(edges_data, geojson_path)

        # Step 5: Try to build SUMO network
        net_file_path = None
        osm_file = network_dir / "roads.osm"
        try:
            # Save OSM XML
            ox.save_graph_xml(graph, filepath=osm_file)
            net_file_path = self._build_sumo_network(osm_file, network_dir)
        except Exception as e:
            logger.warning(f"SUMO network build skipped: {e}")

        # Step 6: Save to database
        num_edges = len(edges_data.get("features", []))
        total_length = sum(
            f["properties"].get("length_m", 0)
            for f in edges_data.get("features", [])
        ) / 1000.0  # Convert to km

        db_network = Network(
            name=name,
            bbox_south=bbox.south,
            bbox_west=bbox.west,
            bbox_north=bbox.north,
            bbox_east=bbox.east,
            net_file=str(net_file_path) if net_file_path else None,
            geojson_file=str(geojson_path),
            num_nodes=graph.number_of_nodes() if graph else 0,
            num_edges=num_edges,
            total_length_km=round(total_length, 2),
            quality_report=quality_report,
        )
        self.db.add(db_network)
        self.db.commit()
        self.db.refresh(db_network)

        logger.info(f"Network '{name}' built: {num_edges} edges, {total_length:.2f} km")

        return NetworkResponse(
            id=db_network.id,
            name=db_network.name,
            bbox=bbox,
            num_nodes=db_network.num_nodes,
            num_edges=db_network.num_edges,
            total_length_km=db_network.total_length_km,
            quality_report=quality_report,
            geojson=edges_data,
            created_at=db_network.created_at,
        )

    def _resolve_bbox(self, request: NetworkBuildRequest) -> tuple[BoundingBox, str]:
        """Resolve bounding box from corridor name or explicit coordinates."""
        if request.corridor_name:
            corridors = get_corridors().get("corridors", {})
            corridor = corridors.get(request.corridor_name)
            if not corridor:
                raise ValueError(
                    f"Unknown corridor '{request.corridor_name}'. "
                    f"Available: {list(corridors.keys())}"
                )
            bb = corridor["bbox"]
            return (
                BoundingBox(
                    south=bb["south"], west=bb["west"],
                    north=bb["north"], east=bb["east"]
                ),
                request.name or corridor["name"],
            )
        
        if request.bbox:
            return request.bbox, request.name or "Custom Area"
        
        # Default: use the default corridor
        corridors_config = get_corridors()
        default_name = corridors_config.get("default_corridor", "ab_road")
        corridors = corridors_config.get("corridors", {})
        corridor = corridors[default_name]
        bb = corridor["bbox"]
        return (
            BoundingBox(
                south=bb["south"], west=bb["west"],
                north=bb["north"], east=bb["east"]
            ),
            corridor["name"],
        )

    def _build_from_osm(self, bbox: BoundingBox) -> tuple:
        """
        Download OSM data and process it into a road network.
        Returns (graph, quality_report, geojson_edges).
        """
        import osmnx as ox
        import geopandas as gpd
        import numpy as np

        logger.info("Downloading OSM road network...")
        
        # Download the drivable road network
        graph = ox.graph_from_bbox(
            bbox=(bbox.north, bbox.south, bbox.east, bbox.west),
            network_type="drive",
            simplify=True,
            retain_all=False,
        )
        
        logger.info(f"Downloaded: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")

        # Convert to GeoDataFrame for processing
        nodes_gdf, edges_gdf = ox.graph_to_gdfs(graph)
        
        # Apply Indian road rules and track quality
        edges_gdf, quality_report = self._apply_indian_rules(edges_gdf)

        # Clean the network
        edges_gdf = self._clean_network(edges_gdf)

        # Convert back to graph (for SUMO export)
        graph = ox.graph_from_gdfs(nodes_gdf, edges_gdf)

        # Build GeoJSON
        geojson = self._edges_to_geojson(edges_gdf)

        return graph, quality_report, geojson

    def _apply_indian_rules(self, edges_gdf) -> tuple:
        """
        Apply Indian road correction rules to OSM edges.
        Estimates missing attributes based on highway class.
        Tracks what was real vs estimated for the quality report.
        """
        import numpy as np
        
        # Initialize quality tracking
        total = len(edges_gdf)
        had_lanes = 0
        had_width = 0
        had_speed = 0
        road_classes = {}

        for idx, row in edges_gdf.iterrows():
            # Get highway type (can be a list in OSMnx)
            highway = row.get("highway", "unclassified")
            if isinstance(highway, list):
                highway = highway[0]
            
            # Count road classes
            road_classes[highway] = road_classes.get(highway, 0) + 1

            # Get defaults for this road class
            defaults = self.road_defaults.get(highway, self.road_defaults.get("unclassified", {}))
            
            # --- Lanes ---
            existing_lanes = row.get("lanes")
            if existing_lanes and str(existing_lanes) not in ("", "nan", "None"):
                had_lanes += 1
                try:
                    lanes_val = int(str(existing_lanes).split(";")[0])
                except (ValueError, IndexError):
                    lanes_val = defaults.get("lanes", 2)
            else:
                lanes_val = defaults.get("lanes", 2)
                # Adjust for bidirectional roads
                oneway = row.get("oneway", False)
                if not oneway and self.rules.get("oneway_lane_adjustment", True):
                    lanes_val = max(1, lanes_val)  # keep as-is, it's per-direction already
            
            edges_gdf.at[idx, "lanes_estimated"] = lanes_val
            
            # --- Width ---
            existing_width = row.get("width")
            if existing_width and str(existing_width) not in ("", "nan", "None"):
                had_width += 1
                try:
                    width_val = float(str(existing_width).replace("m", "").strip().split(";")[0])
                except (ValueError, IndexError):
                    width_val = defaults.get("lane_width_m", 3.0) * lanes_val
            else:
                width_val = defaults.get("lane_width_m", 3.0) * lanes_val
            
            edges_gdf.at[idx, "width_estimated"] = round(width_val, 1)
            
            # --- Speed ---
            existing_speed = row.get("maxspeed")
            if existing_speed and str(existing_speed) not in ("", "nan", "None"):
                had_speed += 1
                try:
                    speed_val = float(str(existing_speed).split(";")[0].replace("mph", "").replace("kmh", "").strip())
                except (ValueError, IndexError):
                    speed_val = defaults.get("speed_kmh", 30)
            else:
                speed_val = defaults.get("speed_kmh", 30)
            
            edges_gdf.at[idx, "speed_kmh"] = speed_val
            edges_gdf.at[idx, "speed_ms"] = round(speed_val / 3.6, 2)
            
            # --- Priority ---
            edges_gdf.at[idx, "priority"] = defaults.get("priority", 5)
            
            # --- Road class label ---
            edges_gdf.at[idx, "road_class"] = highway

        # Build quality report
        quality_report = {
            "total_edges": total,
            "edges_with_lanes_tag": had_lanes,
            "edges_with_width_tag": had_width,
            "edges_with_speed_tag": had_speed,
            "pct_lanes_estimated": round((1 - had_lanes / max(total, 1)) * 100, 1),
            "pct_width_estimated": round((1 - had_width / max(total, 1)) * 100, 1),
            "pct_speed_estimated": round((1 - had_speed / max(total, 1)) * 100, 1),
            "road_class_distribution": road_classes,
        }

        logger.info(
            f"Applied Indian rules: {had_lanes}/{total} had lanes, "
            f"{had_width}/{total} had width, {had_speed}/{total} had speed"
        )

        return edges_gdf, quality_report

    def _clean_network(self, edges_gdf):
        """
        Clean the network by removing tiny edges and disconnected fragments.
        """
        min_length = self.cleaning.get("min_edge_length_m", 5.0)
        
        # Remove very short edges
        if "length" in edges_gdf.columns:
            before = len(edges_gdf)
            edges_gdf = edges_gdf[edges_gdf["length"] >= min_length]
            removed = before - len(edges_gdf)
            if removed > 0:
                logger.info(f"Removed {removed} edges shorter than {min_length}m")

        return edges_gdf

    def _edges_to_geojson(self, edges_gdf) -> dict:
        """Convert edges GeoDataFrame to a GeoJSON dict for the frontend."""
        features = []
        
        for idx, row in edges_gdf.iterrows():
            # Get geometry
            geom = row.geometry
            if geom is None:
                continue
            
            # Build coordinates list
            coords = list(geom.coords) if hasattr(geom, 'coords') else []
            
            # Build properties
            props = {
                "edge_id": str(idx),
                "name": str(row.get("name", "")) if row.get("name") else "",
                "highway": str(row.get("road_class", row.get("highway", ""))),
                "lanes": int(row.get("lanes_estimated", row.get("lanes", 1)) or 1),
                "width_m": float(row.get("width_estimated", 6.0) or 6.0),
                "speed_kmh": float(row.get("speed_kmh", 30) or 30),
                "length_m": round(float(row.get("length", 0) or 0), 1),
                "oneway": bool(row.get("oneway", False)),
                "priority": int(row.get("priority", 5) or 5),
            }
            
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[c[0], c[1]] for c in coords],  # [lon, lat]
                },
                "properties": props,
            }
            features.append(feature)

        return {
            "type": "FeatureCollection",
            "features": features,
        }

    def _build_sumo_network(self, osm_file: Path, output_dir: Path) -> Optional[Path]:
        """
        Convert OSM file to SUMO network using netconvert.
        Returns path to .net.xml if successful, None otherwise.
        """
        if not settings.sumo_available:
            logger.info("SUMO not available, skipping .net.xml generation")
            return None
        
        net_file = output_dir / "network.net.xml"
        
        # Find netconvert binary
        netconvert = "netconvert"
        if settings.sumo_bin_dir:
            netconvert = str(settings.sumo_bin_dir / "netconvert")
        
        cmd = [
            netconvert,
            "--osm-files", str(osm_file),
            "--output-file", str(net_file),
            "--geometry.remove", "true",
            "--ramps.guess", "true",
            "--junctions.join", "true",
            "--tls.guess-signals", "true",
            "--tls.discard-simple", "true",
            "--lefthand",  # India drives on the left
            "--no-turnarounds",
            "--offset.disable-normalization",
        ]
        
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                logger.info(f"SUMO network built: {net_file}")
                return net_file
            else:
                logger.warning(f"netconvert failed: {result.stderr[:500]}")
                return None
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"netconvert error: {e}")
            return None

    def _load_demo_network(self, bbox: BoundingBox, name: str) -> NetworkResponse:
        """
        Load a demo network when OSM download or processing fails.
        Uses bundled demo GeoJSON data.
        """
        logger.info("Loading demo network data...")
        
        # Check for existing demo GeoJSON
        demo_geojson_path = DEMO_DIR / "demo_network.geojson"
        
        if demo_geojson_path.exists():
            geojson = load_json(demo_geojson_path)
        else:
            # Generate a synthetic demo network
            geojson = self._generate_synthetic_network(bbox)
            save_json(geojson, demo_geojson_path)

        num_edges = len(geojson.get("features", []))
        total_length = sum(
            f["properties"].get("length_m", 100) for f in geojson.get("features", [])
        ) / 1000.0

        quality_report = {
            "total_edges": num_edges,
            "edges_with_lanes_tag": 0,
            "edges_with_width_tag": 0,
            "edges_with_speed_tag": 0,
            "pct_lanes_estimated": 100.0,
            "pct_width_estimated": 100.0,
            "pct_speed_estimated": 100.0,
            "road_class_distribution": {"demo": num_edges},
            "note": "DEMO DATA - generated synthetically, not from real OSM"
        }

        # Save to database
        db_network = Network(
            name=f"[DEMO] {name}",
            bbox_south=bbox.south,
            bbox_west=bbox.west,
            bbox_north=bbox.north,
            bbox_east=bbox.east,
            geojson_file=str(demo_geojson_path),
            num_nodes=num_edges + 1,
            num_edges=num_edges,
            total_length_km=round(total_length, 2),
            quality_report=quality_report,
        )
        self.db.add(db_network)
        self.db.commit()
        self.db.refresh(db_network)

        return NetworkResponse(
            id=db_network.id,
            name=db_network.name,
            bbox=bbox,
            num_nodes=db_network.num_nodes,
            num_edges=db_network.num_edges,
            total_length_km=db_network.total_length_km,
            quality_report=quality_report,
            geojson=geojson,
            created_at=db_network.created_at,
        )

    def _generate_synthetic_network(self, bbox: BoundingBox) -> dict:
        """
        Generate a synthetic road network for demo purposes.
        Creates a grid-like pattern of roads within the bounding box.
        """
        import random
        random.seed(42)

        features = []
        edge_id = 0
        
        # Create a grid of roads
        lat_step = (bbox.north - bbox.south) / 6
        lon_step = (bbox.east - bbox.west) / 6
        
        road_classes = ["primary", "secondary", "tertiary", "residential"]
        
        # Horizontal roads
        for i in range(7):
            lat = bbox.south + i * lat_step
            road_class = road_classes[min(i % 4, 3)]
            defaults = self.road_defaults.get(road_class, {})
            
            coords = []
            for j in range(7):
                lon = bbox.west + j * lon_step
                # Add slight randomness
                lat_jitter = lat + random.uniform(-0.0003, 0.0003)
                lon_jitter = lon + random.uniform(-0.0003, 0.0003)
                coords.append([lon_jitter, lat_jitter])
            
            length_m = abs(bbox.east - bbox.west) * 111320 * math.cos(math.radians(lat))
            
            feature = {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coords},
                "properties": {
                    "edge_id": f"edge_{edge_id:03d}",
                    "name": f"Demo Road H{i}",
                    "highway": road_class,
                    "lanes": defaults.get("lanes", 2),
                    "width_m": defaults.get("lane_width_m", 3.0) * defaults.get("lanes", 2),
                    "speed_kmh": defaults.get("speed_kmh", 30),
                    "length_m": round(length_m, 1),
                    "oneway": False,
                    "priority": defaults.get("priority", 5),
                },
            }
            features.append(feature)
            edge_id += 1

        # Vertical roads
        for j in range(7):
            lon = bbox.west + j * lon_step
            road_class = road_classes[min(j % 4, 3)]
            defaults = self.road_defaults.get(road_class, {})
            
            coords = []
            for i in range(7):
                lat = bbox.south + i * lat_step
                lat_jitter = lat + random.uniform(-0.0003, 0.0003)
                lon_jitter = lon + random.uniform(-0.0003, 0.0003)
                coords.append([lon_jitter, lat_jitter])
            
            length_m = abs(bbox.north - bbox.south) * 111320
            
            feature = {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coords},
                "properties": {
                    "edge_id": f"edge_{edge_id:03d}",
                    "name": f"Demo Road V{j}",
                    "highway": road_class,
                    "lanes": defaults.get("lanes", 2),
                    "width_m": defaults.get("lane_width_m", 3.0) * defaults.get("lanes", 2),
                    "speed_kmh": defaults.get("speed_kmh", 30),
                    "length_m": round(length_m, 1),
                    "oneway": False,
                    "priority": defaults.get("priority", 5),
                },
            }
            features.append(feature)
            edge_id += 1

        return {"type": "FeatureCollection", "features": features}
