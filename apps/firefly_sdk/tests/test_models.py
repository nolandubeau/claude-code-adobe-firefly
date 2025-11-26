"""
Tests for Adobe Firefly SDK Models
"""

import pytest
from pydantic import ValidationError

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


class TestImageSize:
    def test_default_values(self):
        size = ImageSize()
        assert size.width == 1024
        assert size.height == 1024

    def test_custom_values(self):
        size = ImageSize(width=1920, height=1080)
        assert size.width == 1920
        assert size.height == 1080

    def test_invalid_width_too_large(self):
        with pytest.raises(ValidationError):
            ImageSize(width=5000, height=1024)

    def test_invalid_height_negative(self):
        with pytest.raises(ValidationError):
            ImageSize(width=1024, height=-100)


class TestPlacement:
    def test_default_values(self):
        placement = Placement()
        assert placement.horizontal_align == "center"
        assert placement.vertical_align == "center"

    def test_custom_alignment(self):
        placement = Placement(horizontal_align="left", vertical_align="top")
        assert placement.horizontal_align == "left"
        assert placement.vertical_align == "top"

    def test_invalid_alignment(self):
        with pytest.raises(ValidationError):
            Placement(horizontal_align="middle")


class TestFireflyImage:
    def test_basic_image(self):
        img = FireflyImage(url="https://example.com/image.jpg")
        assert img.url == "https://example.com/image.jpg"
        assert img.seed is None

    def test_image_with_seed(self):
        img = FireflyImage(url="https://example.com/image.jpg", seed=12345)
        assert img.seed == 12345


class TestGenerateImageRequest:
    def test_minimal_request(self):
        req = GenerateImageRequest(prompt="A beautiful sunset")
        assert req.prompt == "A beautiful sunset"
        assert req.width == 1024
        assert req.height == 1024
        assert req.num_variations == 1
        assert req.content_class is None

    def test_full_request(self):
        req = GenerateImageRequest(
            prompt="A mountain landscape",
            negative_prompt="blurry, low quality",
            width=1920,
            height=1080,
            num_variations=4,
            content_class="photo",
            style="cinematic",
        )
        assert req.prompt == "A mountain landscape"
        assert req.negative_prompt == "blurry, low quality"
        assert req.width == 1920
        assert req.height == 1080
        assert req.num_variations == 4
        assert req.content_class == "photo"
        assert req.style == "cinematic"

    def test_empty_prompt_fails(self):
        with pytest.raises(ValidationError):
            GenerateImageRequest(prompt="")

    def test_too_many_variations(self):
        with pytest.raises(ValidationError):
            GenerateImageRequest(prompt="test", num_variations=5)

    def test_invalid_content_class(self):
        with pytest.raises(ValidationError):
            GenerateImageRequest(prompt="test", content_class="invalid")


class TestExpandImageRequest:
    def test_with_url(self):
        req = ExpandImageRequest(
            image_url="https://example.com/image.jpg",
            prompt="Continue the scene",
        )
        assert req.image_url == "https://example.com/image.jpg"
        assert req.prompt == "Continue the scene"

    def test_with_placement(self):
        req = ExpandImageRequest(
            image_url="https://example.com/image.jpg",
            prompt="Expand left",
            target_width=2048,
            placement=Placement(horizontal_align="right"),
        )
        assert req.target_width == 2048
        assert req.placement.horizontal_align == "right"


class TestFillImageRequest:
    def test_with_urls(self):
        req = FillImageRequest(
            image_url="https://example.com/image.jpg",
            mask_url="https://example.com/mask.png",
            prompt="Add a tree",
        )
        assert req.image_url is not None
        assert req.mask_url is not None
        assert req.prompt == "Add a tree"


class TestRemoveBackgroundRequest:
    def test_with_url(self):
        req = RemoveBackgroundRequest(image_url="https://example.com/image.jpg")
        assert req.image_url == "https://example.com/image.jpg"

    def test_with_base64(self):
        req = RemoveBackgroundRequest(image_base64="base64encodeddata")
        assert req.image_base64 == "base64encodeddata"


class TestGenerateSimilarRequest:
    def test_minimal(self):
        req = GenerateSimilarRequest(
            reference_image_url="https://example.com/ref.jpg"
        )
        assert req.reference_image_url is not None
        assert req.similarity == 0.5
        assert req.num_variations == 1

    def test_with_options(self):
        req = GenerateSimilarRequest(
            reference_image_url="https://example.com/ref.jpg",
            prompt="Make it more vibrant",
            similarity=0.8,
            num_variations=3,
        )
        assert req.prompt == "Make it more vibrant"
        assert req.similarity == 0.8
        assert req.num_variations == 3

    def test_invalid_similarity(self):
        with pytest.raises(ValidationError):
            GenerateSimilarRequest(
                reference_image_url="https://example.com/ref.jpg",
                similarity=1.5,
            )


class TestStyleTransferRequest:
    def test_basic(self):
        req = StyleTransferRequest(
            style_image_url="https://example.com/style.jpg",
            prompt="A city street",
        )
        assert req.style_image_url is not None
        assert req.prompt == "A city street"
        assert req.style_strength == 0.7

    def test_custom_strength(self):
        req = StyleTransferRequest(
            style_image_url="https://example.com/style.jpg",
            prompt="A forest",
            style_strength=0.9,
        )
        assert req.style_strength == 0.9

    def test_invalid_strength(self):
        with pytest.raises(ValidationError):
            StyleTransferRequest(
                style_image_url="https://example.com/style.jpg",
                prompt="test",
                style_strength=-0.1,
            )


class TestGenerateImageResponse:
    def test_response_with_images(self):
        response = GenerateImageResponse(
            images=[
                FireflyImage(url="https://example.com/1.jpg", seed=111),
                FireflyImage(url="https://example.com/2.jpg", seed=222),
            ],
            content_class="photo",
        )
        assert len(response.images) == 2
        assert response.images[0].seed == 111
        assert response.content_class == "photo"

    def test_empty_response(self):
        response = GenerateImageResponse(images=[])
        assert len(response.images) == 0
