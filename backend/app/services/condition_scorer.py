"""
BharatRoad Twin - Condition Scorer Service
===========================================
Computes per-edge Road Condition Scores from damage detections.

Condition Score formula:
    score = min(100, sum(severity_weight * count) / (edge_length_per_100m) * scale_factor)

Penalty derivation:
    speed_penalty = max(min_speed_fraction, 1 - score * penalty_per_point)
    width_penalty = max(min_width_fraction, 1 - score * width_penalty_per_point)
"""

from typing import Optional
from loguru import logger
from sqlalchemy.orm import Session

from app.config import get_road_rules, DEMO_DIR
from app.models import ConditionScore, Detection, Network
from app.schemas import ConditionResponse, ConditionScoreItem, DetectionItem
from app.utils import load_json, clamp


class ConditionScorerService:
    """
    Service for managing road condition scores.
    
    Can load scores from:
    1. Demo data (bundled synthetic detections)
    2. ML inference results (from YOLOv8 detection pipeline)
    """

    def __init__(self, db: Session):
        self.db = db
        self.rules = get_road_rules()
        self.damage_weights = self.rules.get("damage_weights", {})
        self.penalty_config = self.rules.get("condition_penalty", {})

    def load_demo_data(self, network_id: int) -> dict:
        """
        Load synthetic demo condition data from bundled files.
        This allows the full pipeline to work without any ML model.
        """
        logger.info(f"Loading demo condition data for network {network_id}")

        # Load demo detections
        demo_detections_path = DEMO_DIR / "demo_detections.json"
        demo_scores_path = DEMO_DIR / "demo_condition_scores.json"

        if not demo_detections_path.exists() or not demo_scores_path.exists():
            raise FileNotFoundError("Demo data files not found in data/demo/")

        detections_data = load_json(demo_detections_path)
        scores_data = load_json(demo_scores_path)

        # Clear existing data for this network
        self.db.query(ConditionScore).filter(
            ConditionScore.network_id == network_id
        ).delete()
        self.db.query(Detection).filter(
            Detection.network_id == network_id
        ).delete()

        # Insert detections
        detection_count = 0
        for det in detections_data.get("detections", []):
            db_det = Detection(
                network_id=network_id,
                damage_class=det["damage_class"],
                confidence=det["confidence"],
                latitude=det["latitude"],
                longitude=det["longitude"],
                frame_number=det.get("frame_number"),
                matched_edge_id=det.get("matched_edge_id"),
                source="demo",
            )
            self.db.add(db_det)
            detection_count += 1

        # Insert condition scores
        score_count = 0
        for score in scores_data.get("scores", []):
            db_score = ConditionScore(
                network_id=network_id,
                edge_id=score["edge_id"],
                score=score["score"],
                damage_counts=score.get("damage_counts", {}),
                speed_penalty=score.get("speed_penalty", 1.0),
                width_penalty=score.get("width_penalty", 1.0),
                source="demo",
            )
            self.db.add(db_score)
            score_count += 1

        self.db.commit()
        logger.info(f"Loaded {detection_count} detections and {score_count} scores")

        return {
            "message": f"Loaded demo data: {detection_count} detections, {score_count} edge scores",
            "network_id": network_id,
            "source": "demo",
            "total_detections": detection_count,
            "edges_with_damage": score_count,
        }

    def get_scores(self, network_id: int) -> ConditionResponse:
        """
        Get all condition scores and detections for a network.
        """
        # Query scores
        scores = (
            self.db.query(ConditionScore)
            .filter(ConditionScore.network_id == network_id)
            .all()
        )

        # Query detections
        detections = (
            self.db.query(Detection)
            .filter(Detection.network_id == network_id)
            .all()
        )

        # Convert to response format
        score_items = [
            ConditionScoreItem(
                edge_id=s.edge_id,
                score=s.score,
                speed_penalty=s.speed_penalty,
                width_penalty=s.width_penalty,
                damage_counts=s.damage_counts,
            )
            for s in scores
        ]

        detection_items = [
            DetectionItem(
                damage_class=d.damage_class,
                confidence=d.confidence,
                latitude=d.latitude,
                longitude=d.longitude,
                frame_number=d.frame_number,
                matched_edge_id=d.matched_edge_id,
                match_distance_m=d.match_distance_m,
            )
            for d in detections
        ]

        # Calculate average score
        avg_score = (
            sum(s.score for s in scores) / len(scores) if scores else 0.0
        )
        
        source = scores[0].source if scores else "none"

        return ConditionResponse(
            network_id=network_id,
            total_detections=len(detection_items),
            edges_with_damage=len([s for s in score_items if s.score > 0]),
            avg_score=round(avg_score, 1),
            scores=score_items,
            detections=detection_items,
            source=source,
        )

    def compute_score(
        self,
        damage_counts: dict,
        edge_length_m: float = 100.0,
    ) -> tuple[float, float, float]:
        """
        Compute the condition score for an edge from damage counts.
        
        Args:
            damage_counts: Dict of {damage_class: count}, e.g. {"D40": 3, "D20": 1}
            edge_length_m: Length of the edge in meters
        
        Returns:
            (score, speed_penalty, width_penalty)
            - score: 0 (perfect) to 100 (worst)
            - speed_penalty: multiplier 0.3 to 1.0
            - width_penalty: multiplier 0.5 to 1.0
        """
        if not damage_counts or edge_length_m <= 0:
            return 0.0, 1.0, 1.0

        # Compute weighted damage density per 100m
        weighted_sum = 0.0
        for damage_class, count in damage_counts.items():
            weight = self.damage_weights.get(
                damage_class,
                self.damage_weights.get("default", 0.5)
            )
            weighted_sum += weight * count

        # Normalize to per-100m density, then scale to 0-100
        density_per_100m = weighted_sum / (edge_length_m / 100.0)
        
        # Scale factor: 5 weighted damages per 100m → score of 100
        scale_factor = 20.0
        score = clamp(density_per_100m * scale_factor, 0.0, 100.0)

        # Compute penalties
        penalty_per_point = self.penalty_config.get("penalty_per_point", 0.006)
        min_speed = self.penalty_config.get("min_speed_fraction", 0.3)
        speed_penalty = clamp(1.0 - score * penalty_per_point, min_speed, 1.0)

        width_per_point = self.penalty_config.get("width_penalty_per_point", 0.003)
        min_width = self.penalty_config.get("min_width_fraction", 0.5)
        width_penalty = clamp(1.0 - score * width_per_point, min_width, 1.0)

        return round(score, 1), round(speed_penalty, 4), round(width_penalty, 4)
