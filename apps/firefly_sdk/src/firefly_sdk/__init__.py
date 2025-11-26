"""
Adobe Firefly SDK for Python

A comprehensive Python SDK for Adobe Firefly API, designed for use with
Claude Code and Claude Agent SDK.
"""

from firefly_sdk.client import FireflyClient
from firefly_sdk.models import (
    GenerateImageRequest,
    GenerateImageResponse,
    ExpandImageRequest,
    FillImageRequest,
    RemoveBackgroundRequest,
    GenerateSimilarRequest,
    StyleTransferRequest,
    FireflyImage,
    ImageSize,
    Placement,
)

__version__ = "1.0.0"
__all__ = [
    "FireflyClient",
    "GenerateImageRequest",
    "GenerateImageResponse",
    "ExpandImageRequest",
    "FillImageRequest",
    "RemoveBackgroundRequest",
    "GenerateSimilarRequest",
    "StyleTransferRequest",
    "FireflyImage",
    "ImageSize",
    "Placement",
]
