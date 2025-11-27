"""
Adobe Firefly API Client for Python.

This module provides an async client for Adobe Firefly's image generation
and manipulation APIs with comprehensive error handling and retry logic.
"""

import os
import asyncio
import logging
from typing import Any, Optional
from enum import Enum
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

logger = logging.getLogger(__name__)


class FireflyErrorCode(Enum):
    """Error codes for Firefly API errors."""
    AUTH_FAILED = "auth_failed"
    INVALID_CREDENTIALS = "invalid_credentials"
    TOKEN_EXPIRED = "token_expired"
    RATE_LIMITED = "rate_limited"
    INVALID_REQUEST = "invalid_request"
    INVALID_IMAGE = "invalid_image"
    IMAGE_TOO_LARGE = "image_too_large"
    CONTENT_POLICY = "content_policy"
    SERVER_ERROR = "server_error"
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class FireflyAuthError(Exception):
    """Authentication error with Adobe Firefly API."""

    def __init__(self, message: str, code: FireflyErrorCode = FireflyErrorCode.AUTH_FAILED):
        super().__init__(message)
        self.code = code


class FireflyAPIError(Exception):
    """API error from Adobe Firefly."""

    def __init__(
        self,
        message: str,
        status_code: int,
        response_body: str,
        code: FireflyErrorCode = FireflyErrorCode.UNKNOWN,
        retryable: bool = False,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
        self.code = code
        self.retryable = retryable

    @classmethod
    def from_response(cls, status_code: int, response_body: str) -> "FireflyAPIError":
        """Create an appropriate error from an HTTP response."""
        code = FireflyErrorCode.UNKNOWN
        retryable = False
        message = f"API request failed: {status_code}"

        if status_code == 400:
            code = FireflyErrorCode.INVALID_REQUEST
            message = "Invalid request parameters"
        elif status_code == 401:
            code = FireflyErrorCode.TOKEN_EXPIRED
            message = "Authentication token expired"
            retryable = True  # Can retry after re-auth
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

        return cls(message, status_code, response_body, code, retryable)


class FireflyValidationError(Exception):
    """Input validation error."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message)
        self.field = field


class FireflyClient:
    """
    Adobe Firefly API Client.

    Handles OAuth authentication and all Firefly API operations with
    automatic retry logic for transient failures.

    Example:
        async with FireflyClient() as client:
            response = await client.generate_image(
                GenerateImageRequest(prompt="A sunset over mountains")
            )
            print(response.images[0].url)
    """

    AUTH_URL = "https://ims-na1.adobelogin.com/ims/token/v3"
    API_BASE = "https://firefly-api.adobe.io"
    SCOPES = "openid,AdobeID,firefly_api,ff_apis"

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAYS = [1.0, 2.0, 4.0]  # Exponential backoff

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 3,
    ):
        """
        Initialize the Firefly client.

        Args:
            client_id: Adobe Developer Console client ID.
                      Falls back to FIREFLY_CLIENT_ID env var.
            client_secret: Adobe Developer Console client secret.
                          Falls back to FIREFLY_CLIENT_SECRET env var.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries for transient failures.
        """
        self.client_id = client_id or os.getenv("FIREFLY_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("FIREFLY_CLIENT_SECRET")

        if not self.client_id or not self.client_secret:
            raise FireflyAuthError(
                "FIREFLY_CLIENT_ID and FIREFLY_CLIENT_SECRET are required. "
                "Set them as environment variables or pass them to the constructor.",
                FireflyErrorCode.INVALID_CREDENTIALS,
            )

        self._access_token: Optional[str] = None
        self._token_expiry: float = 0
        self._timeout = timeout
        self._max_retries = max_retries
        self._http_client = httpx.AsyncClient(timeout=timeout)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._http_client.aclose()

    async def close(self):
        """Explicitly close the HTTP client."""
        await self._http_client.aclose()

    async def _authenticate(self, force_refresh: bool = False) -> str:
        """
        Get or refresh access token.

        Args:
            force_refresh: Force token refresh even if current token is valid.

        Returns:
            Valid access token.

        Raises:
            FireflyAuthError: If authentication fails.
        """
        import time

        # Return cached token if still valid (with 60s buffer)
        if not force_refresh and self._access_token and time.time() < self._token_expiry - 60:
            return self._access_token

        logger.debug("Authenticating with Adobe IMS...")

        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.SCOPES,
        }

        try:
            response = await self._http_client.post(
                self.AUTH_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except httpx.TimeoutException:
            raise FireflyAuthError(
                "Authentication request timed out",
                FireflyErrorCode.TIMEOUT,
            )
        except httpx.NetworkError as e:
            raise FireflyAuthError(
                f"Network error during authentication: {e}",
                FireflyErrorCode.NETWORK_ERROR,
            )

        if response.status_code != 200:
            if response.status_code == 401:
                raise FireflyAuthError(
                    "Invalid client credentials",
                    FireflyErrorCode.INVALID_CREDENTIALS,
                )
            raise FireflyAuthError(
                f"Authentication failed: {response.status_code} - {response.text}",
                FireflyErrorCode.AUTH_FAILED,
            )

        token_data = response.json()
        self._access_token = token_data["access_token"]
        self._token_expiry = time.time() + token_data["expires_in"]

        logger.debug("Authentication successful, token expires in %d seconds", token_data["expires_in"])

        return self._access_token

    async def _request(
        self,
        endpoint: str,
        body: dict[str, Any],
        retry_count: int = 0,
    ) -> dict[str, Any]:
        """
        Make an authenticated API request with retry logic.

        Args:
            endpoint: API endpoint path.
            body: Request body.
            retry_count: Current retry attempt (internal use).

        Returns:
            Parsed JSON response.

        Raises:
            FireflyAPIError: If the request fails after all retries.
        """
        token = await self._authenticate()

        try:
            response = await self._http_client.post(
                f"{self.API_BASE}{endpoint}",
                json=body,
                headers={
                    "Authorization": f"Bearer {token}",
                    "x-api-key": self.client_id,
                    "Content-Type": "application/json",
                },
            )
        except httpx.TimeoutException:
            if retry_count < self._max_retries:
                logger.warning("Request timed out, retrying (%d/%d)...", retry_count + 1, self._max_retries)
                await asyncio.sleep(self.RETRY_DELAYS[min(retry_count, len(self.RETRY_DELAYS) - 1)])
                return await self._request(endpoint, body, retry_count + 1)
            raise FireflyAPIError(
                "Request timed out",
                0,
                "",
                FireflyErrorCode.TIMEOUT,
                retryable=True,
            )
        except httpx.NetworkError as e:
            if retry_count < self._max_retries:
                logger.warning("Network error, retrying (%d/%d)...", retry_count + 1, self._max_retries)
                await asyncio.sleep(self.RETRY_DELAYS[min(retry_count, len(self.RETRY_DELAYS) - 1)])
                return await self._request(endpoint, body, retry_count + 1)
            raise FireflyAPIError(
                f"Network error: {e}",
                0,
                "",
                FireflyErrorCode.NETWORK_ERROR,
                retryable=True,
            )

        if response.status_code != 200:
            error = FireflyAPIError.from_response(response.status_code, response.text)

            # Handle token expiry with re-auth
            if error.code == FireflyErrorCode.TOKEN_EXPIRED and retry_count == 0:
                logger.info("Token expired, refreshing and retrying...")
                await self._authenticate(force_refresh=True)
                return await self._request(endpoint, body, retry_count + 1)

            # Retry on retryable errors
            if error.retryable and retry_count < self._max_retries:
                delay = self.RETRY_DELAYS[min(retry_count, len(self.RETRY_DELAYS) - 1)]
                logger.warning(
                    "Retryable error (%s), waiting %.1fs before retry (%d/%d)...",
                    error.code.value, delay, retry_count + 1, self._max_retries
                )
                await asyncio.sleep(delay)
                return await self._request(endpoint, body, retry_count + 1)

            raise error

        return response.json()

    def _validate_image_source(
        self,
        image_url: Optional[str],
        image_base64: Optional[str],
        field_name: str = "image",
    ) -> None:
        """Validate that exactly one image source is provided."""
        if not image_url and not image_base64:
            raise FireflyValidationError(
                f"Either {field_name}_url or {field_name}_base64 must be provided",
                field_name,
            )
        if image_url and image_base64:
            raise FireflyValidationError(
                f"Only one of {field_name}_url or {field_name}_base64 should be provided",
                field_name,
            )

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
        }

        # Use aspect_ratio if provided, otherwise use width/height
        if request.aspect_ratio:
            body["aspectRatio"] = request.aspect_ratio
        else:
            body["size"] = {
                "width": request.width,
                "height": request.height,
            }

        if request.negative_prompt:
            body["negativePrompt"] = request.negative_prompt

        if request.content_class:
            body["contentClass"] = request.content_class

        if request.seed is not None:
            body["seed"] = request.seed

        if request.output_format:
            body["outputFormat"] = request.output_format

        if request.prompt_biasing_locale_code:
            body["promptBiasingLocaleCode"] = request.prompt_biasing_locale_code

        # Handle style - can be simple preset string or complex style_options dict
        if request.style_options:
            body["style"] = request.style_options
        elif request.style:
            body["style"] = {"presets": [request.style]}

        if request.structure:
            body["structure"] = request.structure

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
