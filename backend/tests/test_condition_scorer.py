"""
Tests for the Condition Scorer Service.
Covers: score computation, penalty derivation, damage weight application.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.condition_scorer import ConditionScorerService


class TestConditionScoreComputation:
    """Test the condition score formula and penalty derivation."""

    @pytest.fixture
    def scorer(self):
        """Create a scorer with a mock DB session."""
        # We only test compute_score which doesn't use DB
        return ConditionScorerService(db=None)

    def test_perfect_road(self, scorer):
        """A road with no damage should have score 0, no penalties."""
        score, speed_pen, width_pen = scorer.compute_score({}, 100.0)
        assert score == 0.0
        assert speed_pen == 1.0
        assert width_pen == 1.0

    def test_minor_damage(self, scorer):
        """Minor damage (one crack) should give a low score."""
        score, speed_pen, width_pen = scorer.compute_score(
            {"D00": 1},  # One longitudinal crack
            100.0,
        )
        assert 0 < score < 30, f"Expected low score, got {score}"
        assert 0.8 < speed_pen <= 1.0
        assert 0.9 < width_pen <= 1.0

    def test_severe_damage(self, scorer):
        """Multiple potholes should give a high score."""
        score, speed_pen, width_pen = scorer.compute_score(
            {"D40": 5, "D20": 3},  # 5 potholes + 3 alligator cracks
            100.0,
        )
        assert score > 50, f"Expected high score, got {score}"
        assert speed_pen < 0.8

    def test_maximum_score_capped(self, scorer):
        """Score should never exceed 100."""
        score, speed_pen, width_pen = scorer.compute_score(
            {"D40": 50},  # Extreme damage
            100.0,
        )
        assert score <= 100.0

    def test_speed_penalty_has_floor(self, scorer):
        """Speed penalty should never go below minimum fraction."""
        score, speed_pen, width_pen = scorer.compute_score(
            {"D40": 100},  # Absurd damage
            100.0,
        )
        assert speed_pen >= 0.3  # min_speed_fraction from config

    def test_width_penalty_has_floor(self, scorer):
        """Width penalty should never go below minimum fraction."""
        score, speed_pen, width_pen = scorer.compute_score(
            {"D40": 100},
            100.0,
        )
        assert width_pen >= 0.5  # min_width_fraction from config

    def test_pothole_worse_than_crack(self, scorer):
        """Potholes (D40) should produce worse scores than cracks (D00)."""
        score_pothole, _, _ = scorer.compute_score({"D40": 1}, 100.0)
        score_crack, _, _ = scorer.compute_score({"D00": 1}, 100.0)
        assert score_pothole > score_crack

    def test_longer_edge_dilutes_score(self, scorer):
        """Same damage on a longer edge should have a lower density score."""
        score_short, _, _ = scorer.compute_score({"D40": 3}, 100.0)
        score_long, _, _ = scorer.compute_score({"D40": 3}, 500.0)
        assert score_long < score_short

    def test_zero_length_edge(self, scorer):
        """Zero-length edge should return perfect score (edge case)."""
        score, speed_pen, width_pen = scorer.compute_score({"D40": 1}, 0.0)
        assert score == 0.0
        assert speed_pen == 1.0
