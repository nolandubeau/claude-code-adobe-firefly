"""
Adobe Firefly API Client for Python.
"""

import os
from typing import Any, Optional
import httpx
from dotenv import load_dotenv

from firefly_sdk.models import (
    GenerateImageRequest,
    GenerateImageResponse,
    ExpandImageRequest,
    FillImageRequest,
    RemoveBackgroundRequest,
    RemoveBackgroundResponse,
    GenerateSimilarRequest,
    StyleTransferRequest,
    FireflyImage,
)

load_dotenv()


class FireflyAuthError(Exception):
    """Authentication error with Adobe Firefly API."""
    pass


class FireflyAPIError(Exception):
    """API error from Adobe Firefly."""
    def __init__(self, message: str, status_code: int, response_body: str):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class FireflyClient:
    """
    Adobe Firefly API Client.

    Handles OAuth authentication and all Firefly API operations.
    """

    AUTH_URL = "https://ims-na1.adobelogin.com/ims/token/v3"
    API_BASE = "https://firefly-api.adobe.io"
    SCOPES = "openid,AdobeID,firefly_api,ff_apis"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        """
        Initialize the Firefly client.

        Args:
            client_id: Adobe Developer Console client ID.
                      Falls back to FIREFLY_CLIENT_ID env var.
            client_secret: Adobe Developer Console client secret.
                          Falls back to FIREFLY_CLIENT_SECRET env var.
        """
        self.client_id = client_id or os.getenv("FIREFLY_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("FIREFLY_CLIENT_SECRET")

        if not self.client_id or not self.client_secret:
            raise FireflyAuthError(
                "FIREFLY_CLIENT_ID and FIREFLY_CLIENT_SECRET are required. "
                "Set them as environment variables or pass them to the constructor."
            )

        self._access_token: Optional[str] = None
        self._token_expiry: float = 0
        self._http_client = httpx.AsyncClient(timeout=60.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._http_client.aclose()

    async def _authenticate(self) -> str:
        """Get or refresh access token."""
        import time

        # Return cached token if still valid (with 60s buffer)
        if self._access_token and time.time() < self._token_expiry - 60:
            return self._access_token

        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.SCOPES,
        }

        response = await self._http_client.post(
            self.AUTH_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code != 200:
            raise FireflyAuthError(
                f"Authentication failed: {response.status_code} - {response.text}"
            )

        token_data = response.json()
        self._access_token = token_data["access_token"]
        self._token_expiry = time.time() + token_data["expires_in"]

        return self._access_token

    async def _request(
        self,
        endpoint: str,
        body: dict[str, Any],
    ) -> dict[str, Any]:
        """Make an authenticated API request."""
        token = await self._authenticate()

        response = await self._http_client.post(
            f"{self.API_BASE}{endpoint}",
            json=body,
            headers={
                "Authorization": f"Bearer {token}",
                "x-api-key": self.client_id,
                "Content-Type": "application/json",
            },
        )

        if response.status_code != 200:
            raise FireflyAPIError(
                f"API request failed: {response.status_code}",
                response.status_code,
                response.text,
            )

        return response.json()

    async def generate_image(
        self,
        request: GenerateImageRequest,
    ) -> GenerateImageResponse:
        """
        Generate images from a text prompt.

        Args:
            request: Image generation parameters.

        Returns:
            GenerateImageResponse with generated image URLs.
        """
        body: dict[str, Any] = {
            "prompt": request.prompt,
            "n": request.num_variations,
            "size": {
                "width": request.width,
                "height": request.height,
            },
        }

        if request.negative_prompt:
            body["negativePrompt"] = request.negative_prompt

        if request.content_class:
            body["contentClass"] = request.content_class

        if request.style:
            body["style"] = {"presets": [request.style]}

        result = await self._request("/v3/images/generate", body)

        return GenerateImageResponse(
            images=[FireflyImage(**img) for img in result.get("images", [])],
            content_class=result.get("contentClass"),
        )

    async def expand_image(
        self,
        request: ExpandImageRequest,
    ) -> GenerateImageResponse:
        """
        Expand an image beyond its boundaries.

        Args:
            request: Expansion parameters.

        Returns:
            GenerateImageResponse with expanded image URLs.
        """
        body: dict[str, Any] = {"prompt": request.prompt}

        if request.image_url:
            body["image"] = {"source": {"url": request.image_url}}
        elif request.image_base64:
            body["image"] = {"source": {"base64": request.image_base64}}

        if request.target_width or request.target_height:
            body["size"] = {}
            if request.target_width:
                body["size"]["width"] = request.target_width
            if request.target_height:
                body["size"]["height"] = request.target_height

        if request.placement:
            body["placement"] = {
                "alignment": {
                    "horizontal": request.placement.horizontal_align,
                    "vertical": request.placement.vertical_align,
                }
            }

        result = await self._request("/v3/images/expand", body)

        return GenerateImageResponse(
            images=[FireflyImage(**img) for img in result.get("images", [])],
        )

    async def fill_image(
        self,
        request: FillImageRequest,
    ) -> GenerateImageResponse:
        """
        Fill portions of an image using a mask.

        Args:
            request: Fill parameters including mask.

        Returns:
            GenerateImageResponse with filled image URLs.
        """
        body: dict[str, Any] = {"prompt": request.prompt}

        if request.image_url:
            body["image"] = {"source": {"url": request.image_url}}
        elif request.image_base64:
            body["image"] = {"source": {"base64": request.image_base64}}

        if request.mask_url:
            body["mask"] = {"source": {"url": request.mask_url}}
        elif request.mask_base64:
            body["mask"] = {"source": {"base64": request.mask_base64}}

        result = await self._request("/v3/images/fill", body)

        return GenerateImageResponse(
            images=[FireflyImage(**img) for img in result.get("images", [])],
        )

    async def remove_background(
        self,
        request: RemoveBackgroundRequest,
    ) -> RemoveBackgroundResponse:
        """
        Remove the background from an image.

        Args:
            request: Image to process.

        Returns:
            RemoveBackgroundResponse with processed image URL.
        """
        body: dict[str, Any] = {}

        if request.image_url:
            body["image"] = {"source": {"url": request.image_url}}
        elif request.image_base64:
            body["image"] = {"source": {"base64": request.image_base64}}

        result = await self._request("/v2/images/cutout", body)

        return RemoveBackgroundResponse(url=result["output"]["url"])

    async def generate_similar(
        self,
        request: GenerateSimilarRequest,
    ) -> GenerateImageResponse:
        """
        Generate images similar to a reference.

        Args:
            request: Similar image generation parameters.

        Returns:
            GenerateImageResponse with similar image URLs.
        """
        body: dict[str, Any] = {"n": request.num_variations}

        if request.reference_image_url:
            body["image"] = {"source": {"url": request.reference_image_url}}
        elif request.reference_image_base64:
            body["image"] = {"source": {"base64": request.reference_image_base64}}

        if request.prompt:
            body["prompt"] = request.prompt

        if request.similarity is not None:
            body["similarity"] = request.similarity

        result = await self._request("/v3/images/generate-similar", body)

        return GenerateImageResponse(
            images=[FireflyImage(**img) for img in result.get("images", [])],
        )

    async def apply_style_transfer(
        self,
        request: StyleTransferRequest,
    ) -> GenerateImageResponse:
        """
        Apply style from a reference image to new content.

        Args:
            request: Style transfer parameters.

        Returns:
            GenerateImageResponse with styled image URLs.
        """
        body: dict[str, Any] = {"prompt": request.prompt}

        style_config: dict[str, Any] = {"strength": request.style_strength}

        if request.style_image_url:
            style_config["imageReference"] = {"source": {"url": request.style_image_url}}
        elif request.style_image_base64:
            style_config["imageReference"] = {"source": {"base64": request.style_image_base64}}

        body["style"] = style_config

        result = await self._request("/v3/images/generate", body)

        return GenerateImageResponse(
            images=[FireflyImage(**img) for img in result.get("images", [])],
        )
