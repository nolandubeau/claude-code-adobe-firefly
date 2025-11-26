"""
Tests for Adobe Firefly SDK Client
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from firefly_sdk.client import (
    FireflyClient,
    FireflyAuthError,
    FireflyAPIError,
)
from firefly_sdk.models import (
    GenerateImageRequest,
    ExpandImageRequest,
    RemoveBackgroundRequest,
    GenerateSimilarRequest,
    StyleTransferRequest,
)


class TestFireflyClientInit:
    def test_init_with_credentials(self):
        client = FireflyClient(
            client_id="test_id",
            client_secret="test_secret",
        )
        assert client.client_id == "test_id"
        assert client.client_secret == "test_secret"

    def test_init_from_env(self, monkeypatch):
        monkeypatch.setenv("FIREFLY_CLIENT_ID", "env_id")
        monkeypatch.setenv("FIREFLY_CLIENT_SECRET", "env_secret")

        client = FireflyClient()
        assert client.client_id == "env_id"
        assert client.client_secret == "env_secret"

    def test_init_missing_credentials(self, monkeypatch):
        monkeypatch.delenv("FIREFLY_CLIENT_ID", raising=False)
        monkeypatch.delenv("FIREFLY_CLIENT_SECRET", raising=False)

        with pytest.raises(FireflyAuthError):
            FireflyClient()


class TestFireflyClientAuth:
    @pytest.mark.asyncio
    async def test_authentication_success(self):
        client = FireflyClient(
            client_id="test_id",
            client_secret="test_secret",
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_token",
            "expires_in": 3600,
        }

        with patch.object(
            client._http_client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response

            token = await client._authenticate()

            assert token == "test_token"
            assert client._access_token == "test_token"

    @pytest.mark.asyncio
    async def test_authentication_failure(self):
        client = FireflyClient(
            client_id="test_id",
            client_secret="test_secret",
        )

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Invalid credentials"

        with patch.object(
            client._http_client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(FireflyAuthError):
                await client._authenticate()

    @pytest.mark.asyncio
    async def test_token_caching(self):
        client = FireflyClient(
            client_id="test_id",
            client_secret="test_secret",
        )

        # Set cached token with future expiry
        import time
        client._access_token = "cached_token"
        client._token_expiry = time.time() + 3600

        # Should return cached token without making API call
        token = await client._authenticate()
        assert token == "cached_token"


class TestFireflyClientAPI:
    @pytest.fixture
    def authenticated_client(self):
        client = FireflyClient(
            client_id="test_id",
            client_secret="test_secret",
        )
        import time
        client._access_token = "test_token"
        client._token_expiry = time.time() + 3600
        return client

    @pytest.mark.asyncio
    async def test_generate_image(self, authenticated_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "images": [
                {"url": "https://example.com/generated.jpg", "seed": 12345}
            ]
        }

        with patch.object(
            authenticated_client._http_client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response

            request = GenerateImageRequest(prompt="A sunset")
            response = await authenticated_client.generate_image(request)

            assert len(response.images) == 1
            assert response.images[0].url == "https://example.com/generated.jpg"
            assert response.images[0].seed == 12345

    @pytest.mark.asyncio
    async def test_remove_background(self, authenticated_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {"url": "https://example.com/nobg.png"}
        }

        with patch.object(
            authenticated_client._http_client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response

            request = RemoveBackgroundRequest(
                image_url="https://example.com/original.jpg"
            )
            response = await authenticated_client.remove_background(request)

            assert response.url == "https://example.com/nobg.png"

    @pytest.mark.asyncio
    async def test_api_error_handling(self, authenticated_client):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"

        with patch.object(
            authenticated_client._http_client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response

            request = GenerateImageRequest(prompt="test")

            with pytest.raises(FireflyAPIError) as exc_info:
                await authenticated_client.generate_image(request)

            assert exc_info.value.status_code == 400


class TestFireflyClientContextManager:
    @pytest.mark.asyncio
    async def test_context_manager(self):
        async with FireflyClient(
            client_id="test_id",
            client_secret="test_secret",
        ) as client:
            assert client._http_client is not None

    @pytest.mark.asyncio
    async def test_cleanup_on_exit(self):
        client = FireflyClient(
            client_id="test_id",
            client_secret="test_secret",
        )

        await client.__aenter__()
        http_client = client._http_client

        with patch.object(
            http_client, "aclose", new_callable=AsyncMock
        ) as mock_close:
            await client.__aexit__(None, None, None)
            mock_close.assert_called_once()
