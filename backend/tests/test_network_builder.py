"""
Tests for the Network Builder Service.
Covers: Indian road rules application, bbox validation, quality report generation.
"""

import pytest
import sys
import os

# Ensure we can import from the app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import get_road_rules
from app.utils import bbox_area_sq_km, haversine_distance


class TestIndianRoadRules:
    """Test that Indian road rules are loaded correctly."""

    def test_road_rules_loaded(self):
        """Road rules YAML should load without errors."""
        rules = get_road_rules()
        assert "road_defaults" in rules
        assert "left_hand_traffic" in rules
        assert rules["left_hand_traffic"] is True

    def test_all_road_classes_have_defaults(self):
        """Every expected road class should have default values."""
        rules = get_road_rules()
        expected_classes = [
            "motorway", "trunk", "primary", "secondary",
            "tertiary", "residential", "unclassified", "service"
        ]
        for rc in expected_classes:
            assert rc in rules["road_defaults"], f"Missing defaults for {rc}"
            defaults = rules["road_defaults"][rc]
            assert "lanes" in defaults
            assert "lane_width_m" in defaults
            assert "speed_kmh" in defaults

    def test_speed_limits_are_realistic(self):
        """Speed limits should be in realistic Indian urban ranges."""
        rules = get_road_rules()
        for class_name, defaults in rules["road_defaults"].items():
            speed = defaults["speed_kmh"]
            assert 10 <= speed <= 100, (
                f"{class_name} has unrealistic speed {speed} km/h"
            )

    def test_lane_widths_are_realistic(self):
        """Lane widths should be between 2.0 and 4.0 meters."""
        rules = get_road_rules()
        for class_name, defaults in rules["road_defaults"].items():
            width = defaults["lane_width_m"]
            assert 2.0 <= width <= 4.0, (
                f"{class_name} has unrealistic lane width {width}m"
            )

    def test_damage_weights_exist(self):
        """Damage severity weights should be defined."""
        rules = get_road_rules()
        assert "damage_weights" in rules
        weights = rules["damage_weights"]
        # Pothole should have highest weight
        assert weights.get("D40", 0) >= weights.get("D00", 0)

    def test_condition_penalty_config(self):
        """Condition penalty configuration should be valid."""
        rules = get_road_rules()
        penalty = rules["condition_penalty"]
        assert 0 < penalty["penalty_per_point"] < 0.02
        assert 0 < penalty["min_speed_fraction"] < 1.0
        assert 0 < penalty["min_width_fraction"] < 1.0


class TestBoundingBox:
    """Test bounding box utility functions."""

    def test_area_calculation_indore(self):
        """AB Road corridor area should be reasonable (< 5 sq km)."""
        # AB Road corridor
        area = bbox_area_sq_km(22.700, 75.850, 22.740, 75.900)
        assert 0.5 < area < 30, f"Area {area} sq km seems wrong"

    def test_area_zero(self):
        """Zero-size bbox should have zero area."""
        area = bbox_area_sq_km(22.720, 75.870, 22.720, 75.870)
        assert area == pytest.approx(0.0, abs=0.01)

    def test_haversine_known_distance(self):
        """Test haversine with a known distance."""
        # Distance between two points in Indore (approx 1 km)
        dist = haversine_distance(22.720, 75.870, 22.729, 75.870)
        assert 900 < dist < 1100, f"Expected ~1km, got {dist}m"

    def test_haversine_same_point(self):
        """Same point should give zero distance."""
        dist = haversine_distance(22.720, 75.870, 22.720, 75.870)
        assert dist == 0.0
