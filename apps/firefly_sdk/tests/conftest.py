"""
Pytest configuration for Adobe Firefly SDK tests.
"""

import pytest
import sys
from pathlib import Path

# Add the src directory to the path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture(autouse=True)
def reset_env(monkeypatch):
    """Reset environment variables for each test."""
    # Clear any existing Firefly env vars to ensure clean state
    monkeypatch.delenv("FIREFLY_CLIENT_ID", raising=False)
    monkeypatch.delenv("FIREFLY_CLIENT_SECRET", raising=False)
