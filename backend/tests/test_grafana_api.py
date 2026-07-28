"""
Grafana API Test Suite

Tests for Grafana integration endpoints including health checks,
dashboard management, embed URL generation, and metric queries.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from httpx import Response
import json

# Import the Grafana router
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from grafana_api import router as grafana_router


# Create test app
app = FastAPI()
app.include_router(grafana_router)
client = TestClient(app)


class TestGrafanaHealth:
    """Test Grafana health check endpoint"""

    @patch('grafana_api.httpx.AsyncClient')
    async def test_health_check_success(self, mock_client):
        """Test successful health check"""
        # Mock successful Grafana response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "version": "12.2.0",
            "database": "ok"
        }

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance

        # Call endpoint
        response = client.get("/api/v1/monitoring/grafana/health")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data

    @patch('grafana_api.httpx.AsyncClient')
    async def test_health_check_connection_error(self, mock_client):
        """Test health check when Grafana is unreachable"""
        # Mock connection error
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.get = AsyncMock(side_effect=Exception("Connection refused"))
        mock_client.return_value = mock_client_instance

        response = client.get("/api/v1/monitoring/grafana/health")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["status"] in ["unreachable", "error"]


class TestDashboardOperations:
    """Test dashboard listing and retrieval"""

    @patch('grafana_api.httpx.AsyncClient')
    async def test_list_dashboards_success(self, mock_client):
        """Test successful dashboard listing"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"uid": "abc123", "title": "System Metrics", "type": "dash-db"},
            {"uid": "def456", "title": "GPU Monitoring", "type": "dash-db"}
        ]

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance

        response = client.get("/api/v1/monitoring/grafana/dashboards")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 2
        assert len(data["dashboards"]) == 2
        assert data["dashboards"][0]["uid"] == "abc123"

    @patch('grafana_api.httpx.AsyncClient')
    async def test_get_dashboard_by_uid_success(self, mock_client):
        """Test successful dashboard retrieval by UID"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "dashboard": {
                "uid": "abc123",
                "title": "System Metrics",
                "panels": []
            },
            "meta": {"slug": "system-metrics"}
        }

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance

        response = client.get("/api/v1/monitoring/grafana/dashboards/abc123")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "dashboard" in data

    @patch('grafana_api.httpx.AsyncClient')
    async def test_get_dashboard_not_found(self, mock_client):
        """Test dashboard not found error"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Dashboard not found"

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance

        response = client.get("/api/v1/monitoring/grafana/dashboards/nonexistent")

        assert response.status_code == 404


class TestEmbedURL:
    """Test embed URL generation"""

    def test_embed_url_generation_dark_theme(self):
        """Test embed URL generation with dark theme"""
        response = client.get(
            "/api/v1/monitoring/grafana/dashboards/abc123/embed-url",
            params={"theme": "dark", "from_time": "now-6h", "to_time": "now"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "embed_url" in data
        assert "external_url" in data
        assert data["uid"] == "abc123"
        assert data["theme"] == "dark"
        assert "localhost:3102" in data["external_url"]

    def test_embed_url_with_refresh_interval(self):
        """Test embed URL generation with refresh interval"""
        response = client.get(
            "/api/v1/monitoring/grafana/dashboards/def456/embed-url",
            params={
                "theme": "light",
                "refresh": "30s",
                "from_time": "now-1h",
                "to_time": "now"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["refresh"] == "30s"
        assert data["theme"] == "light"
        assert "now-1h" in data["time_range"]["from"]

    def test_embed_url_custom_time_range(self):
        """Test embed URL with custom time range"""
        response = client.get(
            "/api/v1/monitoring/grafana/dashboards/ghi789/embed-url",
            params={
                "from_time": "now-24h",
                "to_time": "now",
                "kiosk": "full"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["time_range"]["from"] == "now-24h"
        assert data["time_range"]["to"] == "now"


class TestDataSourceOperations:
    """Test data source management"""

    @patch('grafana_api.httpx.AsyncClient')
    async def test_list_datasources_success(self, mock_client):
        """Test successful data source listing"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": 1, "name": "Prometheus", "type": "prometheus", "url": "http://prometheus:9090"},
            {"id": 2, "name": "PostgreSQL", "type": "postgres", "url": "postgresql://localhost"}
        ]

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance

        response = client.get("/api/v1/monitoring/grafana/datasources")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 2
        assert len(data["datasources"]) == 2


class TestMetricQueries:
    """Test metric query functionality"""

    @patch('grafana_api.httpx.AsyncClient')
    async def test_query_metrics_success(self, mock_client):
        """Test successful metric query"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": {
                "A": {
                    "frames": [{"data": [1, 2, 3]}]
                }
            }
        }

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance

        response = client.post(
            "/api/v1/monitoring/grafana/query",
            json={
                "datasource": "prometheus",
                "query": "cpu_usage",
                "from": "now-5m",
                "to": "now"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "metadata" in data

    def test_query_without_query_string(self):
        """Test query error when query string is missing"""
        response = client.post(
            "/api/v1/monitoring/grafana/query",
            json={
                "datasource": "prometheus",
                "from": "now-5m",
                "to": "now"
            }
        )

        assert response.status_code == 400


class TestErrorHandling:
    """Test error handling and edge cases"""

    @patch('grafana_api.httpx.AsyncClient')
    async def test_unauthorized_access(self, mock_client):
        """Test unauthorized access handling"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance

        response = client.get(
            "/api/v1/monitoring/grafana/dashboards",
            params={"api_key": "invalid_key"}
        )

        assert response.status_code == 401

    def test_invalid_dashboard_uid(self):
        """Test handling of invalid dashboard UID format"""
        response = client.get(
            "/api/v1/monitoring/grafana/dashboards//embed-url"
        )

        assert response.status_code in [404, 422]


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
