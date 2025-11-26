"""
Pydantic models for Adobe Firefly API requests and responses.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class ImageSize(BaseModel):
    """Image dimensions."""
    width: int = Field(default=1024, ge=1, le=4096)
    height: int = Field(default=1024, ge=1, le=4096)


class Placement(BaseModel):
    """Placement configuration for image expansion."""
    horizontal_align: Literal["left", "center", "right"] = "center"
    vertical_align: Literal["top", "center", "bottom"] = "center"


class ImageSource(BaseModel):
    """Image source - either URL or base64."""
    url: Optional[str] = None
    base64: Optional[str] = None


class FireflyImage(BaseModel):
    """Generated image result."""
    url: str
    seed: Optional[int] = None


class GenerateImageRequest(BaseModel):
    """Request model for image generation."""
    prompt: str = Field(..., min_length=1, max_length=10000)
    negative_prompt: Optional[str] = Field(default=None, max_length=10000)
    width: int = Field(default=1024, ge=1, le=4096)
    height: int = Field(default=1024, ge=1, le=4096)
    num_variations: int = Field(default=1, ge=1, le=4)
    content_class: Optional[Literal["photo", "art"]] = None
    style: Optional[str] = None


class GenerateImageResponse(BaseModel):
    """Response model for image generation."""
    images: list[FireflyImage]
    content_class: Optional[str] = None


class ExpandImageRequest(BaseModel):
    """Request model for image expansion."""
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    prompt: str = Field(..., min_length=1)
    target_width: Optional[int] = Field(default=None, ge=1, le=4096)
    target_height: Optional[int] = Field(default=None, ge=1, le=4096)
    placement: Optional[Placement] = None


class FillImageRequest(BaseModel):
    """Request model for generative fill."""
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    mask_url: Optional[str] = None
    mask_base64: Optional[str] = None
    prompt: str = Field(..., min_length=1)


class RemoveBackgroundRequest(BaseModel):
    """Request model for background removal."""
    image_url: Optional[str] = None
    image_base64: Optional[str] = None


class RemoveBackgroundResponse(BaseModel):
    """Response model for background removal."""
    url: str


class GenerateSimilarRequest(BaseModel):
    """Request model for similar image generation."""
    reference_image_url: Optional[str] = None
    reference_image_base64: Optional[str] = None
    prompt: Optional[str] = None
    num_variations: int = Field(default=1, ge=1, le=4)
    similarity: float = Field(default=0.5, ge=0.0, le=1.0)


class StyleTransferRequest(BaseModel):
    """Request model for style transfer."""
    style_image_url: Optional[str] = None
    style_image_base64: Optional[str] = None
    prompt: str = Field(..., min_length=1)
    style_strength: float = Field(default=0.7, ge=0.0, le=1.0)
