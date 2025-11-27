"""
Tests for Adobe Firefly MCP Server.

Tests cover:
- All MCP tools
- Error handling
- Parameter validation
- FireflyClient functionality
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio

# Import server components
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from server import (
    FireflyClient,
    FireflyError,
    FireflyErrorCode,
    get_client,
    generate_image,
    expand_image,
    fill_image,
    remove_background,
    generate_similar_images,
    apply_style_transfer,
    mcp,
)


# Mock responses
MOCK_TOKEN_RESPONSE = {
    "access_token": "mock_token",
    "expires_in": 3600,
}

MOCK_GENERATE_RESPONSE = {
    "size": {"width": 1024, "height": 1024},
    "images": [{"url": "https://mock.url/image.png", "seed": 12345}],
    "contentClass": "art",
}

MOCK_EXPAND_RESPONSE = {
    "images": [{"url": "https://mock.url/expanded.png", "seed": 23456}],
}

MOCK_FILL_RESPONSE = {
    "images": [{"url": "https://mock.url/filled.png", "seed": 34567}],
}

MOCK_CUTOUT_RESPONSE = {
    "output": {"url": "https://mock.url/cutout.png"},
}

MOCK_SIMILAR_RESPONSE = {
    "images": [{"url": "https://mock.url/similar.png", "seed": 45678}],
}


class TestFireflyErrorCode:
    """Tests for FireflyErrorCode enum."""

    def test_error_codes_exist(self):
        """Test that all expected error codes exist."""
        assert FireflyErrorCode.AUTH_FAILED
        assert FireflyErrorCode.INVALID_CREDENTIALS
        assert FireflyErrorCode.TOKEN_EXPIRED
        assert FireflyErrorCode.RATE_LIMITED
        assert FireflyErrorCode.INVALID_REQUEST
        assert FireflyErrorCode.IMAGE_TOO_LARGE
        assert FireflyErrorCode.CONTENT_POLICY
        assert FireflyErrorCode.SERVER_ERROR
        assert FireflyErrorCode.NETWORK_ERROR
        assert FireflyErrorCode.TIMEOUT
        assert FireflyErrorCode.UNKNOWN


class TestFireflyError:
    """Tests for FireflyError exception."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = FireflyError("Test error")
        assert str(error) == "Test error"
        assert error.code == FireflyErrorCode.UNKNOWN
        assert error.status_code is None
        assert error.retryable is False

    def test_error_with_code(self):
        """Test error with specific code."""
        error = FireflyError(
            "Auth failed",
            code=FireflyErrorCode.AUTH_FAILED,
            status_code=401,
            retryable=False,
        )
        assert error.code == FireflyErrorCode.AUTH_FAILED
        assert error.status_code == 401

    def test_from_response_400(self):
        """Test error creation from 400 response."""
        error = FireflyError.from_response(400, "Bad request")
        assert error.code == FireflyErrorCode.INVALID_REQUEST
        assert error.status_code == 400
        assert not error.retryable

    def test_from_response_401(self):
        """Test error creation from 401 response."""
        error = FireflyError.from_response(401, "Unauthorized")
        assert error.code == FireflyErrorCode.TOKEN_EXPIRED
        assert error.retryable is True

    def test_from_response_403(self):
        """Test error creation from 403 response."""
        error = FireflyError.from_response(403, "Content policy violation")
        assert error.code == FireflyErrorCode.CONTENT_POLICY
        assert not error.retryable

    def test_from_response_413(self):
        """Test error creation from 413 response."""
        error = FireflyError.from_response(413, "Image too large")
        assert error.code == FireflyErrorCode.IMAGE_TOO_LARGE
        assert not error.retryable

    def test_from_response_429(self):
        """Test error creation from 429 response."""
        error = FireflyError.from_response(429, "Rate limited")
        assert error.code == FireflyErrorCode.RATE_LIMITED
        assert error.retryable is True

    def test_from_response_500(self):
        """Test error creation from 500 response."""
        error = FireflyError.from_response(500, "Server error")
        assert error.code == FireflyErrorCode.SERVER_ERROR
        assert error.retryable is True


class TestFireflyClient:
    """Tests for FireflyClient class."""

    def test_client_initialization(self):
        """Test client initialization."""
        client = FireflyClient("test_id", "test_secret")
        assert client.client_id == "test_id"
        assert client.client_secret == "test_secret"
        assert client.max_retries == 3

    def test_client_custom_retries(self):
        """Test client with custom retries."""
        client = FireflyClient("test_id", "test_secret", max_retries=5)
        assert client.max_retries == 5

    @pytest.mark.asyncio
    async def test_authenticate_success(self, mock_response):
        """Test successful authentication."""
        client = FireflyClient("test_id", "test_secret")

        mock_http_response = mock_response(MOCK_TOKEN_RESPONSE)

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_http_client.post = AsyncMock(return_value=mock_http_response)
            mock_get_client.return_value = mock_http_client

            token = await client._authenticate()
            assert token == "mock_token"

    @pytest.mark.asyncio
    async def test_authenticate_invalid_credentials(self, mock_response):
        """Test authentication with invalid credentials."""
        client = FireflyClient("test_id", "test_secret")

        mock_http_response = mock_response({"error": "invalid"}, status_code=401)

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_http_client.post = AsyncMock(return_value=mock_http_response)
            mock_get_client.return_value = mock_http_client

            with pytest.raises(FireflyError) as exc_info:
                await client._authenticate()

            assert exc_info.value.code == FireflyErrorCode.INVALID_CREDENTIALS


class TestGetClient:
    """Tests for get_client function."""

    def test_get_client_missing_credentials(self):
        """Test get_client without credentials."""
        # Reset the global client
        import server
        server._client = None

        with pytest.raises(FireflyError) as exc_info:
            get_client()

        assert exc_info.value.code == FireflyErrorCode.INVALID_CREDENTIALS

    def test_get_client_with_credentials(self, mock_env):
        """Test get_client with credentials."""
        import server
        server._client = None

        client = get_client()
        assert client is not None
        assert client.client_id == "mock_client_id"

        # Reset for other tests
        server._client = None


class TestGenerateImageTool:
    """Tests for generate_image MCP tool."""

    @pytest.mark.asyncio
    async def test_generate_image_basic(self, mock_env, mock_response):
        """Test basic image generation."""
        import server
        server._client = None

        with patch.object(FireflyClient, "_authenticate", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "mock_token"

            with patch.object(FireflyClient, "_get_client") as mock_get_client:
                mock_http_client = AsyncMock()
                mock_http_response = mock_response(MOCK_GENERATE_RESPONSE)
                mock_http_client.post = AsyncMock(return_value=mock_http_response)
                mock_get_client.return_value = mock_http_client

                result = await generate_image(prompt="a cat coding")

                assert "images" in result
                assert len(result["images"]) == 1
                assert result["images"][0]["url"] == "https://mock.url/image.png"
                assert result["content_class"] == "art"

        server._client = None

    @pytest.mark.asyncio
    async def test_generate_image_with_all_params(self, mock_env, mock_response):
        """Test image generation with all parameters."""
        import server
        server._client = None

        with patch.object(FireflyClient, "_authenticate", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "mock_token"

            with patch.object(FireflyClient, "_get_client") as mock_get_client:
                mock_http_client = AsyncMock()
                mock_http_response = mock_response(MOCK_GENERATE_RESPONSE)
                mock_http_client.post = AsyncMock(return_value=mock_http_response)
                mock_get_client.return_value = mock_http_client

                result = await generate_image(
                    prompt="a cat coding",
                    negative_prompt="no dogs",
                    width=512,
                    height=512,
                    num_variations=2,
                    content_class="photo",
                    style="bw",
                    seed=12345,
                    aspect_ratio="16:9",
                    output_format="png",
                    prompt_biasing_locale_code="en-US",
                    style_options={"presets": ["dramatic"]},
                    structure={"strength": 0.8},
                )

                assert "images" in result

        server._client = None


class TestExpandImageTool:
    """Tests for expand_image MCP tool."""

    @pytest.mark.asyncio
    async def test_expand_image_basic(self, mock_env, mock_response):
        """Test basic image expansion."""
        import server
        server._client = None

        with patch.object(FireflyClient, "_authenticate", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "mock_token"

            with patch.object(FireflyClient, "_get_client") as mock_get_client:
                mock_http_client = AsyncMock()
                mock_http_response = mock_response(MOCK_EXPAND_RESPONSE)
                mock_http_client.post = AsyncMock(return_value=mock_http_response)
                mock_get_client.return_value = mock_http_client

                result = await expand_image(
                    prompt="extend the sky",
                    image_url="https://example.com/image.jpg",
                )

                assert "images" in result

        server._client = None


class TestFillImageTool:
    """Tests for fill_image MCP tool."""

    @pytest.mark.asyncio
    async def test_fill_image_basic(self, mock_env, mock_response):
        """Test basic image fill."""
        import server
        server._client = None

        with patch.object(FireflyClient, "_authenticate", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "mock_token"

            with patch.object(FireflyClient, "_get_client") as mock_get_client:
                mock_http_client = AsyncMock()
                mock_http_response = mock_response(MOCK_FILL_RESPONSE)
                mock_http_client.post = AsyncMock(return_value=mock_http_response)
                mock_get_client.return_value = mock_http_client

                result = await fill_image(
                    prompt="add a sunset",
                    image_url="https://example.com/image.jpg",
                    mask_url="https://example.com/mask.jpg",
                )

                assert "images" in result

        server._client = None


class TestRemoveBackgroundTool:
    """Tests for remove_background MCP tool."""

    @pytest.mark.asyncio
    async def test_remove_background_basic(self, mock_env, mock_response):
        """Test basic background removal."""
        import server
        server._client = None

        with patch.object(FireflyClient, "_authenticate", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "mock_token"

            with patch.object(FireflyClient, "_get_client") as mock_get_client:
                mock_http_client = AsyncMock()
                mock_http_response = mock_response(MOCK_CUTOUT_RESPONSE)
                mock_http_client.post = AsyncMock(return_value=mock_http_response)
                mock_get_client.return_value = mock_http_client

                result = await remove_background(image_url="https://example.com/image.jpg")

                assert "url" in result
                assert result["url"] == "https://mock.url/cutout.png"

        server._client = None

    @pytest.mark.asyncio
    async def test_remove_background_no_image(self, mock_env):
        """Test background removal without image."""
        import server
        server._client = None

        with pytest.raises(FireflyError) as exc_info:
            await remove_background()

        assert exc_info.value.code == FireflyErrorCode.INVALID_REQUEST

        server._client = None


class TestGenerateSimilarTool:
    """Tests for generate_similar_images MCP tool."""

    @pytest.mark.asyncio
    async def test_generate_similar_basic(self, mock_env, mock_response):
        """Test basic similar image generation."""
        import server
        server._client = None

        with patch.object(FireflyClient, "_authenticate", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "mock_token"

            with patch.object(FireflyClient, "_get_client") as mock_get_client:
                mock_http_client = AsyncMock()
                mock_http_response = mock_response(MOCK_SIMILAR_RESPONSE)
                mock_http_client.post = AsyncMock(return_value=mock_http_response)
                mock_get_client.return_value = mock_http_client

                result = await generate_similar_images(
                    reference_image_url="https://example.com/image.jpg",
                )

                assert "images" in result

        server._client = None

    @pytest.mark.asyncio
    async def test_generate_similar_no_reference(self, mock_env):
        """Test similar generation without reference."""
        import server
        server._client = None

        with pytest.raises(FireflyError) as exc_info:
            await generate_similar_images()

        assert exc_info.value.code == FireflyErrorCode.INVALID_REQUEST

        server._client = None


class TestStyleTransferTool:
    """Tests for apply_style_transfer MCP tool."""

    @pytest.mark.asyncio
    async def test_style_transfer_basic(self, mock_env, mock_response):
        """Test basic style transfer."""
        import server
        server._client = None

        with patch.object(FireflyClient, "_authenticate", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "mock_token"

            with patch.object(FireflyClient, "_get_client") as mock_get_client:
                mock_http_client = AsyncMock()
                mock_http_response = mock_response(MOCK_GENERATE_RESPONSE)
                mock_http_client.post = AsyncMock(return_value=mock_http_response)
                mock_get_client.return_value = mock_http_client

                result = await apply_style_transfer(
                    prompt="a cityscape",
                    style_image_url="https://example.com/style.jpg",
                )

                assert "images" in result

        server._client = None

    @pytest.mark.asyncio
    async def test_style_transfer_no_style_image(self, mock_env):
        """Test style transfer without style image."""
        import server
        server._client = None

        with pytest.raises(FireflyError) as exc_info:
            await apply_style_transfer(prompt="a cityscape")

        assert exc_info.value.code == FireflyErrorCode.INVALID_REQUEST

        server._client = None


class TestMCPServer:
    """Tests for MCP server configuration."""

    def test_mcp_server_name(self):
        """Test MCP server name."""
        assert mcp.name == "Adobe Firefly"

    def test_mcp_server_has_instructions(self):
        """Test MCP server has instructions."""
        assert mcp.instructions is not None
        assert "Generate and manipulate images" in mcp.instructions
