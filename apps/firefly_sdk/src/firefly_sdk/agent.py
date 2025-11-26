#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "httpx>=0.27.0",
#   "pydantic>=2.5.0",
#   "python-dotenv>=1.0.0",
#   "rich>=13.7.0",
# ]
# ///
"""
Adobe Firefly Agent Integration

This module provides integration with Claude Agent SDK for building
autonomous creative workflows with Adobe Firefly.
"""

import asyncio
import os
from typing import Any, Optional
from dataclasses import dataclass

from firefly_sdk.client import FireflyClient
from firefly_sdk.models import (
    GenerateImageRequest,
    ExpandImageRequest,
    FillImageRequest,
    RemoveBackgroundRequest,
    GenerateSimilarRequest,
    StyleTransferRequest,
)


@dataclass
class FireflyToolResult:
    """Result from a Firefly tool execution."""
    success: bool
    data: dict[str, Any]
    error: Optional[str] = None


class FireflyAgentTools:
    """
    Adobe Firefly tools for use with Claude Agent SDK.

    Provides tool definitions and execution methods that can be registered
    with a Claude agent for autonomous image generation workflows.
    """

    TOOL_DEFINITIONS = [
        {
            "name": "firefly_generate_image",
            "description": "Generate an image using Adobe Firefly AI from a text prompt.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Text description of the image to generate"
                    },
                    "width": {
                        "type": "integer",
                        "description": "Image width in pixels (default: 1024)"
                    },
                    "height": {
                        "type": "integer",
                        "description": "Image height in pixels (default: 1024)"
                    },
                    "num_variations": {
                        "type": "integer",
                        "description": "Number of variations to generate (1-4)"
                    },
                    "content_class": {
                        "type": "string",
                        "enum": ["photo", "art"],
                        "description": "Style class for generation"
                    },
                    "negative_prompt": {
                        "type": "string",
                        "description": "What to exclude from the image"
                    }
                },
                "required": ["prompt"]
            }
        },
        {
            "name": "firefly_expand_image",
            "description": "Expand an image beyond its boundaries using generative AI.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "image_url": {
                        "type": "string",
                        "description": "URL of the image to expand"
                    },
                    "prompt": {
                        "type": "string",
                        "description": "Description of the expanded content"
                    },
                    "target_width": {
                        "type": "integer",
                        "description": "Target width in pixels"
                    },
                    "target_height": {
                        "type": "integer",
                        "description": "Target height in pixels"
                    }
                },
                "required": ["image_url", "prompt"]
            }
        },
        {
            "name": "firefly_fill_image",
            "description": "Fill or replace portions of an image using a mask.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "image_url": {
                        "type": "string",
                        "description": "URL of the source image"
                    },
                    "mask_url": {
                        "type": "string",
                        "description": "URL of the mask image"
                    },
                    "prompt": {
                        "type": "string",
                        "description": "Description of the fill content"
                    }
                },
                "required": ["image_url", "mask_url", "prompt"]
            }
        },
        {
            "name": "firefly_remove_background",
            "description": "Remove the background from an image.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "image_url": {
                        "type": "string",
                        "description": "URL of the image to process"
                    }
                },
                "required": ["image_url"]
            }
        },
        {
            "name": "firefly_generate_similar",
            "description": "Generate images similar to a reference image.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "reference_url": {
                        "type": "string",
                        "description": "URL of the reference image"
                    },
                    "prompt": {
                        "type": "string",
                        "description": "Optional guiding prompt"
                    },
                    "similarity": {
                        "type": "number",
                        "description": "Similarity to reference (0-1)"
                    },
                    "num_variations": {
                        "type": "integer",
                        "description": "Number of variations (1-4)"
                    }
                },
                "required": ["reference_url"]
            }
        },
        {
            "name": "firefly_style_transfer",
            "description": "Apply the style of a reference image to new content.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "style_url": {
                        "type": "string",
                        "description": "URL of the style reference image"
                    },
                    "prompt": {
                        "type": "string",
                        "description": "Description of content to generate"
                    },
                    "style_strength": {
                        "type": "number",
                        "description": "Strength of style application (0-1)"
                    }
                },
                "required": ["style_url", "prompt"]
            }
        }
    ]

    def __init__(self, client: Optional[FireflyClient] = None):
        """Initialize with optional existing client."""
        self._client = client
        self._owned_client = client is None

    async def __aenter__(self):
        if self._client is None:
            self._client = FireflyClient()
            await self._client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._owned_client and self._client:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)

    async def execute_tool(
        self,
        tool_name: str,
        tool_input: dict[str, Any]
    ) -> FireflyToolResult:
        """Execute a Firefly tool by name."""
        try:
            if tool_name == "firefly_generate_image":
                return await self._generate_image(tool_input)
            elif tool_name == "firefly_expand_image":
                return await self._expand_image(tool_input)
            elif tool_name == "firefly_fill_image":
                return await self._fill_image(tool_input)
            elif tool_name == "firefly_remove_background":
                return await self._remove_background(tool_input)
            elif tool_name == "firefly_generate_similar":
                return await self._generate_similar(tool_input)
            elif tool_name == "firefly_style_transfer":
                return await self._style_transfer(tool_input)
            else:
                return FireflyToolResult(
                    success=False,
                    data={},
                    error=f"Unknown tool: {tool_name}"
                )
        except Exception as e:
            return FireflyToolResult(
                success=False,
                data={},
                error=str(e)
            )

    async def _generate_image(self, params: dict) -> FireflyToolResult:
        request = GenerateImageRequest(
            prompt=params["prompt"],
            width=params.get("width", 1024),
            height=params.get("height", 1024),
            num_variations=params.get("num_variations", 1),
            content_class=params.get("content_class"),
            negative_prompt=params.get("negative_prompt"),
        )
        response = await self._client.generate_image(request)
        return FireflyToolResult(
            success=True,
            data={
                "images": [
                    {"url": img.url, "seed": img.seed}
                    for img in response.images
                ]
            }
        )

    async def _expand_image(self, params: dict) -> FireflyToolResult:
        request = ExpandImageRequest(
            image_url=params["image_url"],
            prompt=params["prompt"],
            target_width=params.get("target_width"),
            target_height=params.get("target_height"),
        )
        response = await self._client.expand_image(request)
        return FireflyToolResult(
            success=True,
            data={"images": [{"url": img.url} for img in response.images]}
        )

    async def _fill_image(self, params: dict) -> FireflyToolResult:
        request = FillImageRequest(
            image_url=params["image_url"],
            mask_url=params["mask_url"],
            prompt=params["prompt"],
        )
        response = await self._client.fill_image(request)
        return FireflyToolResult(
            success=True,
            data={"images": [{"url": img.url} for img in response.images]}
        )

    async def _remove_background(self, params: dict) -> FireflyToolResult:
        request = RemoveBackgroundRequest(image_url=params["image_url"])
        response = await self._client.remove_background(request)
        return FireflyToolResult(
            success=True,
            data={"url": response.url}
        )

    async def _generate_similar(self, params: dict) -> FireflyToolResult:
        request = GenerateSimilarRequest(
            reference_image_url=params["reference_url"],
            prompt=params.get("prompt"),
            similarity=params.get("similarity", 0.5),
            num_variations=params.get("num_variations", 1),
        )
        response = await self._client.generate_similar(request)
        return FireflyToolResult(
            success=True,
            data={"images": [{"url": img.url} for img in response.images]}
        )

    async def _style_transfer(self, params: dict) -> FireflyToolResult:
        request = StyleTransferRequest(
            style_image_url=params["style_url"],
            prompt=params["prompt"],
            style_strength=params.get("style_strength", 0.7),
        )
        response = await self._client.apply_style_transfer(request)
        return FireflyToolResult(
            success=True,
            data={"images": [{"url": img.url} for img in response.images]}
        )


# Example usage with Claude Agent SDK (when available)
async def create_firefly_agent_tools():
    """Create Firefly tools for use with Claude Agent SDK."""
    tools = FireflyAgentTools()
    await tools.__aenter__()
    return tools


if __name__ == "__main__":
    # Demo tool definitions
    import json
    for tool in FireflyAgentTools.TOOL_DEFINITIONS:
        print(f"\n{tool['name']}:")
        print(f"  {tool['description']}")
