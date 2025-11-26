"""
Adobe Firefly SDK for Python

A comprehensive Python SDK for Adobe Firefly API, designed for use with
Claude Code and Claude Agent SDK.
"""

from firefly_sdk.client import (
    FireflyClient,
    FireflyAuthError,
    FireflyAPIError,
    FireflyValidationError,
    FireflyErrorCode,
)
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
    ImageSize,
    Placement,
)

__version__ = "1.0.0"
__all__ = [
    # Client
    "FireflyClient",
    # Errors
    "FireflyAuthError",
    "FireflyAPIError",
    "FireflyValidationError",
    "FireflyErrorCode",
    # Request models
    "GenerateImageRequest",
    "ExpandImageRequest",
    "FillImageRequest",
    "RemoveBackgroundRequest",
    "GenerateSimilarRequest",
    "StyleTransferRequest",
    # Response models
    "GenerateImageResponse",
    "RemoveBackgroundResponse",
    "FireflyImage",
    # Common types
    "ImageSize",
    "Placement",
]
