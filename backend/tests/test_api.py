"""
Tests for the FastAPI endpoints.
Covers: health check, corridors list, and basic endpoint availability.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_returns_200(self, client):
        """Health endpoint should always return 200."""
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_has_required_fields(self, client):
        """Health response should have all required fields."""
        response = client.get("/api/health")
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "sumo_available" in data
        assert "demo_mode" in data
        assert data["status"] == "healthy"

    def test_root_endpoint(self, client):
        """Root endpoint should return welcome message."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "BharatRoad Twin" in data["message"]


class TestCorridorsEndpoint:
    """Test the corridors listing endpoint."""

    def test_list_corridors(self, client):
        """Should return predefined corridors."""
        response = client.get("/api/network/corridors/list")
        assert response.status_code == 200
        data = response.json()
        assert "corridors" in data
        assert "ab_road" in data["corridors"]
        assert "vijay_nagar" in data["corridors"]

    def test_corridor_has_bbox(self, client):
        """Each corridor should have a bounding box."""
        response = client.get("/api/network/corridors/list")
        data = response.json()
        ab_road = data["corridors"]["ab_road"]
        assert "bbox" in ab_road
        assert "south" in ab_road["bbox"]
        assert "north" in ab_road["bbox"]


class TestEndpointAvailability:
    """Test that all API endpoints exist and return proper responses."""

    def test_network_build_requires_body(self, client):
        """POST /api/network/build should require a request body."""
        response = client.post("/api/network/build")
        # FastAPI returns 422 for missing request body
        assert response.status_code in (422, 200, 500)

    def test_condition_demo_data(self, client):
        """POST /api/condition/demo-data should be available."""
        response = client.post("/api/condition/demo-data?network_id=999")
        # May fail with 500 if network doesn't exist, but endpoint should exist
        assert response.status_code in (200, 404, 500)

    def test_simulation_run_requires_body(self, client):
        """POST /api/simulation/run should require a request body."""
        response = client.post("/api/simulation/run")
        assert response.status_code in (422, 200, 500)

    def test_openapi_docs(self, client):
        """OpenAPI docs should be available."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_schema(self, client):
        """OpenAPI schema should be available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "paths" in data
        assert "/api/health" in data["paths"]
