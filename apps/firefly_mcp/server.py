#!/usr/bin/env python3
"""
Adobe Firefly MCP Server

MCP server that provides AI image generation capabilities using Adobe Firefly's
API. Supports image generation, expansion, fill, background removal, similar
image generation, and style transfer.

Usage:
    uv run mcp dev server.py
    uv run mcp install server.py

Environment Variables:
    FIREFLY_CLIENT_ID: Adobe Developer Console client ID
    FIREFLY_CLIENT_SECRET: Adobe Developer Console client secret
"""

import asyncio
import os
import time
from enum import Enum
from typing import Any, Literal, Optional

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

load_dotenv()

# Initialize FastMCP server
mcp = FastMCP(
    "Adobe Firefly",
    instructions=(
        "Generate and manipulate images using Adobe Firefly AI. "
        "Create images from text prompts, expand images beyond boundaries, "
        "fill masked regions, remove backgrounds, generate similar images, "
        "and apply style transfer from reference images."
    ),
)


# ========================================
# Firefly Client Implementation
# ========================================


class FireflyErrorCode(Enum):
    """Error codes for Firefly API errors."""

    AUTH_FAILED = "auth_failed"
    INVALID_CREDENTIALS = "invalid_credentials"
    TOKEN_EXPIRED = "token_expired"
    RATE_LIMITED = "rate_limited"
    INVALID_REQUEST = "invalid_request"
    IMAGE_TOO_LARGE = "image_too_large"
    CONTENT_POLICY = "content_policy"
    SERVER_ERROR = "server_error"
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class FireflyError(Exception):
    """Custom error for Firefly API errors."""

    def __init__(
        self,
        message: str,
        code: FireflyErrorCode = FireflyErrorCode.UNKNOWN,
        status_code: Optional[int] = None,
        retryable: bool = False,
    ):
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.retryable = retryable

    @classmethod
    def from_response(cls, status_code: int, response_body: str) -> "FireflyError":
        """Create error from HTTP response."""
        code = FireflyErrorCode.UNKNOWN
        retryable = False
        message = f"API request failed: {status_code}"

        if status_code == 400:
            code = FireflyErrorCode.INVALID_REQUEST
            message = f"Invalid request: {response_body}"
        elif status_code == 401:
            code = FireflyErrorCode.TOKEN_EXPIRED
            message = "Authentication token expired"
            retryable = True
        elif status_code == 403:
            code = FireflyErrorCode.CONTENT_POLICY
            message = "Request blocked by content policy"
        elif status_code == 413:
            code = FireflyErrorCode.IMAGE_TOO_LARGE
            message = "Image exceeds maximum size"
        elif status_code == 429:
            code = FireflyErrorCode.RATE_LIMITED
            message = "Rate limit exceeded"
            retryable = True
        elif status_code >= 500:
            code = FireflyErrorCode.SERVER_ERROR
            message = "Adobe Firefly server error"
            retryable = True

        return cls(message, code, status_code, retryable)


class FireflyClient:
    """Adobe Firefly API client with authentication and retry logic."""

    AUTH_URL = "https://ims-na1.adobelogin.com/ims/token/v3"
    API_BASE = "https://firefly-api.adobe.io"
    SCOPES = "openid,AdobeID,firefly_api,ff_apis"
    RETRY_DELAYS = [1.0, 2.0, 4.0]

    def __init__(self, client_id: str, client_secret: str, max_retries: int = 3):
        self.client_id = client_id
        self.client_secret = client_secret
        self.max_retries = max_retries
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=60.0)
        return self._http_client

    async def close(self):
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def _authenticate(self, force_refresh: bool = False) -> str:
        """Authenticate and get access token."""
        if not force_refresh and self._access_token and time.time() < self._token_expiry - 60:
            return self._access_token

        client = await self._get_client()
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.SCOPES,
        }

        try:
            response = await client.post(
                self.AUTH_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except httpx.TimeoutException:
            raise FireflyError("Authentication timed out", FireflyErrorCode.TIMEOUT)
        except httpx.NetworkError as e:
            raise FireflyError(f"Network error: {e}", FireflyErrorCode.NETWORK_ERROR)

        if response.status_code != 200:
            if response.status_code == 401:
                raise FireflyError(
                    "Invalid credentials", FireflyErrorCode.INVALID_CREDENTIALS, 401
                )
            raise FireflyError(
                f"Auth failed: {response.text}", FireflyErrorCode.AUTH_FAILED, response.status_code
            )

        token_data = response.json()
        self._access_token = token_data["access_token"]
        self._token_expiry = time.time() + token_data["expires_in"]
        return self._access_token

    async def _request(
        self, endpoint: str, body: dict[str, Any], retry_count: int = 0
    ) -> dict[str, Any]:
        """Make authenticated API request with retry logic."""
        token = await self._authenticate()
        client = await self._get_client()

        try:
            response = await client.post(
                f"{self.API_BASE}{endpoint}",
                json=body,
                headers={
                    "Authorization": f"Bearer {token}",
                    "x-api-key": self.client_id,
                    "Content-Type": "application/json",
                },
            )
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            if retry_count < self.max_retries:
                await asyncio.sleep(self.RETRY_DELAYS[min(retry_count, 2)])
                return await self._request(endpoint, body, retry_count + 1)
            raise FireflyError(f"Request failed: {e}", FireflyErrorCode.NETWORK_ERROR)

        if response.status_code != 200:
            error = FireflyError.from_response(response.status_code, response.text)

            if error.code == FireflyErrorCode.TOKEN_EXPIRED and retry_count == 0:
                await self._authenticate(force_refresh=True)
                return await self._request(endpoint, body, retry_count + 1)

            if error.retryable and retry_count < self.max_retries:
                await asyncio.sleep(self.RETRY_DELAYS[min(retry_count, 2)])
                return await self._request(endpoint, body, retry_count + 1)

            raise error

        return response.json()


# Global client instance
_client: Optional[FireflyClient] = None


def get_client() -> FireflyClient:
    """Get or create Firefly client."""
    global _client
    if _client is None:
        client_id = os.getenv("FIREFLY_CLIENT_ID")
        client_secret = os.getenv("FIREFLY_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise FireflyError(
                "FIREFLY_CLIENT_ID and FIREFLY_CLIENT_SECRET environment variables required",
                FireflyErrorCode.INVALID_CREDENTIALS,
            )
        _client = FireflyClient(client_id, client_secret)
    return _client


# ========================================
# Response Models
# ========================================


class GeneratedImage(BaseModel):
    """A generated image result."""

    url: str
    seed: Optional[int] = None


class ImageGenerationResult(BaseModel):
    """Result from image generation operations."""

    images: list[GeneratedImage]
    content_class: Optional[str] = None


class BackgroundRemovalResult(BaseModel):
    """Result from background removal."""

    url: str


# ========================================
# Image Generation Tool
# ========================================


@mcp.tool()
async def generate_image(
    prompt: str,
    negative_prompt: Optional[str] = None,
    width: int = 1024,
    height: int = 1024,
    num_variations: int = 1,
    content_class: Optional[Literal["photo", "art"]] = None,
    style: Optional[str] = None,
    seed: Optional[int] = None,
    aspect_ratio: Optional[str] = None,
    output_format: Optional[Literal["jpeg", "png"]] = None,
    prompt_biasing_locale_code: Optional[str] = None,
    style_options: Optional[dict] = None,
    structure: Optional[dict] = None,
) -> dict:
    """
    Generate images from a text prompt using Adobe Firefly AI.

    Args:
        prompt: Text description of the image to generate. Be descriptive for best results.
        negative_prompt: Text describing what should NOT appear in the image.
        width: Width of generated image in pixels (default: 1024, max: 4096).
        height: Height of generated image in pixels (default: 1024, max: 4096).
        num_variations: Number of image variations to generate (1-4).
        content_class: Content type - "photo" for photorealistic, "art" for artistic styles.
        style: Optional style preset name to apply.
        seed: Seed for deterministic output (same seed = same image).
        aspect_ratio: Aspect ratio e.g. "1:1", "16:9", "4:3" (alternative to width/height).
        output_format: Output format - "jpeg" or "png".
        prompt_biasing_locale_code: Locale code for prompt biasing, e.g. "en-US", "zh-CN".
        style_options: Complex style object with presets, imageReference, strength.
        structure: Structure reference object for composition guidance.

    Returns:
        Dict with generated image URLs and metadata.
    """
    client = get_client()

    body: dict[str, Any] = {
        "prompt": prompt,
        "n": min(max(num_variations, 1), 4),
    }

    # Use aspect_ratio if provided, otherwise use width/height
    if aspect_ratio:
        body["aspectRatio"] = aspect_ratio
    else:
        body["size"] = {"width": width, "height": height}

    if negative_prompt:
        body["negativePrompt"] = negative_prompt
    if content_class:
        body["contentClass"] = content_class
    if seed is not None:
        body["seed"] = seed
    if output_format:
        body["outputFormat"] = output_format
    if prompt_biasing_locale_code:
        body["promptBiasingLocaleCode"] = prompt_biasing_locale_code

    # Handle style - can be simple preset or complex style_options dict
    if style_options:
        body["style"] = style_options
    elif style:
        body["style"] = {"presets": [style]}

    if structure:
        body["structure"] = structure

    result = await client._request("/v3/images/generate", body)

    return {
        "images": [{"url": img["url"], "seed": img.get("seed")} for img in result.get("images", [])],
        "content_class": result.get("contentClass"),
    }


# ========================================
# Image Expansion Tool
# ========================================


@mcp.tool()
async def expand_image(
    prompt: str,
    image_url: Optional[str] = None,
    image_base64: Optional[str] = None,
    target_width: Optional[int] = None,
    target_height: Optional[int] = None,
    horizontal_align: Literal["left", "center", "right"] = "center",
    vertical_align: Literal["top", "center", "bottom"] = "center",
) -> dict:
    """
    Expand an image beyond its current boundaries using generative AI.

    Args:
        prompt: Text describing what should appear in the expanded area.
        image_url: URL of the source image to expand.
        image_base64: Base64-encoded image data (alternative to image_url).
        target_width: Target width of expanded image in pixels.
        target_height: Target height of expanded image in pixels.
        horizontal_align: Horizontal alignment of original image (left/center/right).
        vertical_align: Vertical alignment of original image (top/center/bottom).

    Returns:
        Dict with expanded image URLs.
    """
    client = get_client()

    body: dict[str, Any] = {"prompt": prompt}

    if image_url:
        body["image"] = {"source": {"url": image_url}}
    elif image_base64:
        body["image"] = {"source": {"base64": image_base64}}

    if target_width or target_height:
        body["size"] = {}
        if target_width:
            body["size"]["width"] = target_width
        if target_height:
            body["size"]["height"] = target_height

    body["placement"] = {
        "alignment": {"horizontal": horizontal_align, "vertical": vertical_align}
    }

    result = await client._request("/v3/images/expand", body)

    return {
        "images": [{"url": img["url"], "seed": img.get("seed")} for img in result.get("images", [])]
    }


# ========================================
# Generative Fill Tool
# ========================================


@mcp.tool()
async def fill_image(
    prompt: str,
    image_url: Optional[str] = None,
    image_base64: Optional[str] = None,
    mask_url: Optional[str] = None,
    mask_base64: Optional[str] = None,
) -> dict:
    """
    Fill or replace portions of an image using a mask and generative AI.

    Args:
        prompt: Text describing what should appear in the masked/filled area.
        image_url: URL of the source image.
        image_base64: Base64-encoded source image (alternative to image_url).
        mask_url: URL of mask image. White areas will be filled, black preserved.
        mask_base64: Base64-encoded mask image (alternative to mask_url).

    Returns:
        Dict with filled image URLs.
    """
    client = get_client()

    body: dict[str, Any] = {"prompt": prompt}

    if image_url:
        body["image"] = {"source": {"url": image_url}}
    elif image_base64:
        body["image"] = {"source": {"base64": image_base64}}

    if mask_url:
        body["mask"] = {"source": {"url": mask_url}}
    elif mask_base64:
        body["mask"] = {"source": {"base64": mask_base64}}

    result = await client._request("/v3/images/fill", body)

    return {
        "images": [{"url": img["url"], "seed": img.get("seed")} for img in result.get("images", [])]
    }


# ========================================
# Background Removal Tool
# ========================================


@mcp.tool()
async def remove_background(
    image_url: Optional[str] = None,
    image_base64: Optional[str] = None,
) -> dict:
    """
    Remove the background from an image, leaving only the main subject.

    Args:
        image_url: URL of the image to process.
        image_base64: Base64-encoded image data (alternative to image_url).

    Returns:
        Dict with URL of the processed image (transparent background).
    """
    if not image_url and not image_base64:
        raise FireflyError(
            "Either image_url or image_base64 must be provided",
            FireflyErrorCode.INVALID_REQUEST,
        )

    client = get_client()

    body: dict[str, Any] = {}
    if image_url:
        body["image"] = {"source": {"url": image_url}}
    elif image_base64:
        body["image"] = {"source": {"base64": image_base64}}

    result = await client._request("/v2/images/cutout", body)

    return {"url": result["output"]["url"]}


# ========================================
# Similar Image Generation Tool
# ========================================


@mcp.tool()
async def generate_similar_images(
    reference_image_url: Optional[str] = None,
    reference_image_base64: Optional[str] = None,
    prompt: Optional[str] = None,
    num_variations: int = 1,
    similarity: float = 0.5,
) -> dict:
    """
    Generate images similar to a reference image.

    Args:
        reference_image_url: URL of the reference image.
        reference_image_base64: Base64-encoded reference image (alternative to URL).
        prompt: Optional text to guide the similar image generation.
        num_variations: Number of variations to generate (1-4).
        similarity: How similar results should be (0.0-1.0). Higher = more similar.

    Returns:
        Dict with similar image URLs.
    """
    if not reference_image_url and not reference_image_base64:
        raise FireflyError(
            "Either reference_image_url or reference_image_base64 must be provided",
            FireflyErrorCode.INVALID_REQUEST,
        )

    client = get_client()

    body: dict[str, Any] = {"n": min(max(num_variations, 1), 4)}

    if reference_image_url:
        body["image"] = {"source": {"url": reference_image_url}}
    elif reference_image_base64:
        body["image"] = {"source": {"base64": reference_image_base64}}

    if prompt:
        body["prompt"] = prompt

    body["similarity"] = max(0.0, min(1.0, similarity))

    result = await client._request("/v3/images/generate-similar", body)

    return {
        "images": [{"url": img["url"], "seed": img.get("seed")} for img in result.get("images", [])]
    }


# ========================================
# Style Transfer Tool
# ========================================


@mcp.tool()
async def apply_style_transfer(
    prompt: str,
    style_image_url: Optional[str] = None,
    style_image_base64: Optional[str] = None,
    style_strength: float = 0.7,
) -> dict:
    """
    Apply the visual style of a reference image to generate new content.

    Args:
        prompt: Text describing the content to generate with the applied style.
        style_image_url: URL of the style reference image.
        style_image_base64: Base64-encoded style image (alternative to URL).
        style_strength: How strongly to apply the style (0.0-1.0). Higher = stronger.

    Returns:
        Dict with styled image URLs.
    """
    if not style_image_url and not style_image_base64:
        raise FireflyError(
            "Either style_image_url or style_image_base64 must be provided",
            FireflyErrorCode.INVALID_REQUEST,
        )

    client = get_client()

    body: dict[str, Any] = {"prompt": prompt}

    strength = max(0.0, min(1.0, style_strength))

    if style_image_url:
        body["style"] = {
            "imageReference": {"source": {"url": style_image_url}},
            "strength": strength,
        }
    elif style_image_base64:
        body["style"] = {
            "imageReference": {"source": {"base64": style_image_base64}},
            "strength": strength,
        }

    result = await client._request("/v3/images/generate", body)

    return {
        "images": [{"url": img["url"], "seed": img.get("seed")} for img in result.get("images", [])]
    }


if __name__ == "__main__":
    mcp.run()
