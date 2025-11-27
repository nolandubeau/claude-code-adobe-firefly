"""
Mock infrastructure for testing Firefly SDK without API credentials.

This module provides mock responses for all Firefly API endpoints,
enabling testing without actual API calls.
"""

import os
from contextlib import contextmanager
from typing import Generator
from unittest.mock import patch, AsyncMock, MagicMock

# Mock URLs and data
MOCK_IMAGE_URL = "https://firefly-mock.adobe.io/mock-generated-image.png"
MOCK_EXPAND_URL = "https://firefly-mock.adobe.io/mock-expanded-image.png"
MOCK_FILL_URL = "https://firefly-mock.adobe.io/mock-filled-image.png"
MOCK_CUTOUT_URL = "https://firefly-mock.adobe.io/mock-cutout-image.png"
MOCK_SIMILAR_URL = "https://firefly-mock.adobe.io/mock-similar-image.png"
MOCK_STYLE_URL = "https://firefly-mock.adobe.io/mock-styled-image.png"

# Standard mock responses
MOCK_TOKEN_RESPONSE = {
    "access_token": "mock_access_token_12345",
    "expires_in": 3600,
    "token_type": "bearer",
}

MOCK_GENERATE_RESPONSE = {
    "size": {"width": 1024, "height": 1024},
    "images": [
        {"url": MOCK_IMAGE_URL, "seed": 123456},
    ],
    "contentClass": "art",
}

MOCK_EXPAND_RESPONSE = {
    "images": [
        {"url": MOCK_EXPAND_URL, "seed": 234567},
    ],
}

MOCK_FILL_RESPONSE = {
    "images": [
        {"url": MOCK_FILL_URL, "seed": 345678},
    ],
}

MOCK_CUTOUT_RESPONSE = {
    "output": {"url": MOCK_CUTOUT_URL},
}

MOCK_SIMILAR_RESPONSE = {
    "images": [
        {"url": MOCK_SIMILAR_URL, "seed": 456789},
    ],
}

MOCK_STYLE_RESPONSE = {
    "images": [
        {"url": MOCK_STYLE_URL, "seed": 567890},
    ],
}


def get_mock_response(endpoint: str) -> dict:
    """Get mock response for a given endpoint."""
    endpoint_responses = {
        "/v3/images/generate": MOCK_GENERATE_RESPONSE,
        "/v3/images/expand": MOCK_EXPAND_RESPONSE,
        "/v3/images/fill": MOCK_FILL_RESPONSE,
        "/v2/images/cutout": MOCK_CUTOUT_RESPONSE,
        "/v3/images/generate-similar": MOCK_SIMILAR_RESPONSE,
    }
    return endpoint_responses.get(endpoint, MOCK_GENERATE_RESPONSE)


class MockHttpxResponse:
    """Mock httpx response."""

    def __init__(self, json_data: dict, status_code: int = 200):
        self._json_data = json_data
        self.status_code = status_code
        self.text = str(json_data)

    def json(self):
        return self._json_data


class MockHttpxClient:
    """Mock async httpx client for testing."""

    def __init__(self):
        self.requests = []

    async def post(self, url: str, **kwargs) -> MockHttpxResponse:
        self.requests.append({"url": url, "kwargs": kwargs})

        # Auth endpoint
        if "ims-na1.adobelogin.com" in url:
            return MockHttpxResponse(MOCK_TOKEN_RESPONSE)

        # API endpoints
        if "firefly-api.adobe.io" in url:
            for endpoint, response in [
                ("/v3/images/generate", MOCK_GENERATE_RESPONSE),
                ("/v3/images/expand", MOCK_EXPAND_RESPONSE),
                ("/v3/images/fill", MOCK_FILL_RESPONSE),
                ("/v2/images/cutout", MOCK_CUTOUT_RESPONSE),
                ("/v3/images/generate-similar", MOCK_SIMILAR_RESPONSE),
            ]:
                if endpoint in url:
                    return MockHttpxResponse(response)

        return MockHttpxResponse(MOCK_GENERATE_RESPONSE)

    async def aclose(self):
        pass


@contextmanager
def use_firefly_mocks() -> Generator[MockHttpxClient, None, None]:
    """
    Context manager for mocking Firefly API calls.

    Usage:
        with use_firefly_mocks() as mock_client:
            # Your test code here
            pass

    This mocks:
    - Adobe IMS token endpoint
    - All Firefly API endpoints
    - Environment variables for credentials
    """
    mock_client = MockHttpxClient()

    # Set mock environment variables
    env_patches = {
        "FIREFLY_CLIENT_ID": "mock_client_id",
        "FIREFLY_CLIENT_SECRET": "mock_client_secret",
    }

    with patch.dict(os.environ, env_patches):
        with patch("httpx.AsyncClient", return_value=mock_client):
            yield mock_client


@contextmanager
def use_sync_firefly_mocks() -> Generator[MockHttpxClient, None, None]:
    """
    Context manager for mocking Firefly API calls in sync context.

    For use with CLI testing where we need to mock the async client
    but run in a sync test context.
    """
    mock_client = MockHttpxClient()

    env_patches = {
        "FIREFLY_CLIENT_ID": "mock_client_id",
        "FIREFLY_CLIENT_SECRET": "mock_client_secret",
    }

    with patch.dict(os.environ, env_patches):
        with patch("firefly_sdk.client.httpx.AsyncClient", return_value=mock_client):
            yield mock_client


# Test image data (1x1 transparent PNG)
MOCK_IMAGE_BYTES = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
    b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
)
