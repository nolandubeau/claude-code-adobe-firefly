"""
Pytest configuration for Adobe Firefly MCP Server tests.
"""

import pytest
import sys
from pathlib import Path

# Add the server directory to the path for imports
server_path = Path(__file__).parent.parent
sys.path.insert(0, str(server_path))


@pytest.fixture(autouse=True)
def reset_env(monkeypatch):
    """Reset environment variables for each test."""
    monkeypatch.delenv("FIREFLY_CLIENT_ID", raising=False)
    monkeypatch.delenv("FIREFLY_CLIENT_SECRET", raising=False)


@pytest.fixture
def mock_env(monkeypatch):
    """Set up mock environment variables."""
    monkeypatch.setenv("FIREFLY_CLIENT_ID", "mock_client_id")
    monkeypatch.setenv("FIREFLY_CLIENT_SECRET", "mock_client_secret")


@pytest.fixture
def mock_response():
    """Mock HTTP response factory."""
    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self._json_data = json_data
            self.status_code = status_code
            self.text = str(json_data)

        def json(self):
            return self._json_data

    return MockResponse
