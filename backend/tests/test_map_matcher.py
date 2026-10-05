"""
Tests for the Map Matcher Service.
Covers: point-to-segment distance, edge matching, batch matching.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.map_matcher import MapMatcherService


class TestMapMatcher:
    """Test map matching functionality."""

    @pytest.fixture
    def matcher(self):
        """Create a matcher with 50m threshold."""
        return MapMatcherService(max_distance_m=50.0)

    @pytest.fixture
    def sample_edges(self):
        """Create sample road edges for testing."""
        return [
            {
                "edge_id": "edge_A",
                "coordinates": [
                    [75.870, 22.720],  # [lon, lat]
                    [75.875, 22.720],
                ],
            },
            {
                "edge_id": "edge_B",
                "coordinates": [
                    [75.870, 22.725],
                    [75.875, 22.725],
                ],
            },
            {
                "edge_id": "edge_C",
                "coordinates": [
                    [75.880, 22.720],
                    [75.880, 22.730],
                ],
            },
        ]

    def test_point_on_edge(self, matcher, sample_edges):
        """A point exactly on an edge should match with near-zero distance."""
        edge_id, distance = matcher.match_detection(
            22.720, 75.872, sample_edges
        )
        assert edge_id == "edge_A"
        assert distance is not None
        assert distance < 5.0  # Should be very close

    def test_point_closer_to_edge_b(self, matcher, sample_edges):
        """A point near edge_B should match to edge_B."""
        edge_id, distance = matcher.match_detection(
            22.7248, 75.872, sample_edges
        )
        assert edge_id == "edge_B"

    def test_point_too_far(self, matcher, sample_edges):
        """A point far from all edges should not match."""
        edge_id, distance = matcher.match_detection(
            22.750, 75.900, sample_edges
        )
        assert edge_id is None
        assert distance is None

    def test_batch_matching(self, matcher, sample_edges):
        """Batch matching should process all detections."""
        detections = [
            {"latitude": 22.720, "longitude": 75.872},
            {"latitude": 22.725, "longitude": 75.873},
            {"latitude": 22.750, "longitude": 75.900},  # too far
        ]
        results = matcher.match_detections_batch(detections, sample_edges)
        assert len(results) == 3
        assert results[0]["matched_edge_id"] == "edge_A"
        assert results[1]["matched_edge_id"] == "edge_B"
        assert results[2]["matched_edge_id"] is None

    def test_empty_edges(self, matcher):
        """Matching against empty edges should return None."""
        edge_id, distance = matcher.match_detection(22.720, 75.870, [])
        assert edge_id is None

    def test_degenerate_edge(self, matcher):
        """Edge with same start and end point should still work."""
        edges = [{
            "edge_id": "degenerate",
            "coordinates": [[75.870, 22.720], [75.870, 22.720]],
        }]
        edge_id, distance = matcher.match_detection(22.720, 75.870, edges)
        assert edge_id == "degenerate"
        assert distance is not None
        assert distance < 1.0
