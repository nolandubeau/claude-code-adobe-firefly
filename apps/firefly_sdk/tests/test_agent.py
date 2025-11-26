"""
Tests for Adobe Firefly Agent Tools Integration
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from firefly_sdk.agent import FireflyAgentTools, FireflyToolResult


class TestFireflyToolResult:
    def test_success_result(self):
        result = FireflyToolResult(
            success=True,
            data={"images": [{"url": "https://example.com/img.jpg"}]},
        )
        assert result.success is True
        assert result.error is None
        assert "images" in result.data

    def test_error_result(self):
        result = FireflyToolResult(
            success=False,
            data={},
            error="API connection failed",
        )
        assert result.success is False
        assert result.error == "API connection failed"


class TestFireflyAgentToolDefinitions:
    def test_all_tools_defined(self):
        tools = FireflyAgentTools.TOOL_DEFINITIONS
        tool_names = [t["name"] for t in tools]

        assert "firefly_generate_image" in tool_names
        assert "firefly_expand_image" in tool_names
        assert "firefly_fill_image" in tool_names
        assert "firefly_remove_background" in tool_names
        assert "firefly_generate_similar" in tool_names
        assert "firefly_style_transfer" in tool_names

    def test_tool_schemas_valid(self):
        for tool in FireflyAgentTools.TOOL_DEFINITIONS:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
            assert tool["input_schema"]["type"] == "object"
            assert "properties" in tool["input_schema"]

    def test_generate_image_schema(self):
        tools = FireflyAgentTools.TOOL_DEFINITIONS
        generate_tool = next(
            t for t in tools if t["name"] == "firefly_generate_image"
        )

        props = generate_tool["input_schema"]["properties"]
        assert "prompt" in props
        assert "width" in props
        assert "height" in props
        assert "num_variations" in props
        assert "content_class" in props

        assert "prompt" in generate_tool["input_schema"]["required"]


class TestFireflyAgentToolsExecution:
    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client.generate_image = AsyncMock()
        client.expand_image = AsyncMock()
        client.fill_image = AsyncMock()
        client.remove_background = AsyncMock()
        client.generate_similar = AsyncMock()
        client.apply_style_transfer = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_execute_generate_image(self, mock_client):
        from firefly_sdk.models import GenerateImageResponse, FireflyImage

        mock_client.generate_image.return_value = GenerateImageResponse(
            images=[FireflyImage(url="https://example.com/img.jpg", seed=123)]
        )

        tools = FireflyAgentTools(client=mock_client)
        tools._client = mock_client

        result = await tools.execute_tool(
            "firefly_generate_image",
            {"prompt": "A sunset", "content_class": "photo"},
        )

        assert result.success is True
        assert len(result.data["images"]) == 1
        assert result.data["images"][0]["url"] == "https://example.com/img.jpg"

    @pytest.mark.asyncio
    async def test_execute_remove_background(self, mock_client):
        from firefly_sdk.models import RemoveBackgroundResponse

        mock_client.remove_background.return_value = RemoveBackgroundResponse(
            url="https://example.com/nobg.png"
        )

        tools = FireflyAgentTools(client=mock_client)
        tools._client = mock_client

        result = await tools.execute_tool(
            "firefly_remove_background",
            {"image_url": "https://example.com/photo.jpg"},
        )

        assert result.success is True
        assert result.data["url"] == "https://example.com/nobg.png"

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self, mock_client):
        tools = FireflyAgentTools(client=mock_client)
        tools._client = mock_client

        result = await tools.execute_tool(
            "firefly_unknown_tool",
            {},
        )

        assert result.success is False
        assert "Unknown tool" in result.error

    @pytest.mark.asyncio
    async def test_execute_tool_exception(self, mock_client):
        mock_client.generate_image.side_effect = Exception("API Error")

        tools = FireflyAgentTools(client=mock_client)
        tools._client = mock_client

        result = await tools.execute_tool(
            "firefly_generate_image",
            {"prompt": "test"},
        )

        assert result.success is False
        assert "API Error" in result.error


class TestFireflyAgentToolsContextManager:
    @pytest.mark.asyncio
    async def test_creates_client_when_none_provided(self):
        with patch("firefly_sdk.agent.FireflyClient") as MockClient:
            mock_instance = MagicMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            MockClient.return_value = mock_instance

            tools = FireflyAgentTools()
            await tools.__aenter__()

            MockClient.assert_called_once()
            mock_instance.__aenter__.assert_called_once()

    @pytest.mark.asyncio
    async def test_uses_provided_client(self):
        mock_client = MagicMock()

        tools = FireflyAgentTools(client=mock_client)
        await tools.__aenter__()

        assert tools._client is mock_client
