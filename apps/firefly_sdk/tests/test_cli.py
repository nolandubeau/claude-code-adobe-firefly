"""
Tests for Adobe Firefly CLI.

Tests cover:
- All CLI commands with mock mode
- Parameter validation
- Output formats (text and JSON)
- Error handling
- Verbose mode
"""

import json
import pytest
from typer.testing import CliRunner
from unittest import mock

from firefly_sdk.cli import app
from firefly_sdk.mocks import (
    MOCK_IMAGE_URL,
    MOCK_EXPAND_URL,
    MOCK_CUTOUT_URL,
    MOCK_SIMILAR_URL,
    MOCK_STYLE_URL,
)

runner = CliRunner()


class TestGenerateCommand:
    """Tests for the generate command."""

    def test_generate_with_mocks(self):
        """Test generate command with mock API."""
        result = runner.invoke(app, ["generate", "a cat coding", "--use-mocks"])
        assert result.exit_code == 0
        assert "Generated image URL:" in result.output
        assert MOCK_IMAGE_URL in result.output

    def test_generate_with_mocks_verbose(self):
        """Test generate with verbose output."""
        result = runner.invoke(
            app, ["generate", "a cat coding", "--use-mocks", "--verbose"]
        )
        assert result.exit_code == 0
        assert "Using mock API responses" in result.output

    def test_generate_with_mocks_json_format(self):
        """Test generate with JSON output format."""
        result = runner.invoke(
            app, ["generate", "a cat coding", "--use-mocks", "--format", "json"]
        )
        assert result.exit_code == 0
        # Should contain JSON output
        assert "images" in result.output
        assert "outputs" in result.output or "url" in result.output

    def test_generate_with_seed(self):
        """Test generate with seed parameter."""
        result = runner.invoke(
            app, ["generate", "a cat coding", "--use-mocks", "--seed", "12345"]
        )
        assert result.exit_code == 0
        assert "Generated image URL:" in result.output

    def test_generate_with_aspect_ratio(self):
        """Test generate with aspect ratio."""
        result = runner.invoke(
            app, ["generate", "a cat coding", "--use-mocks", "--aspect-ratio", "16:9"]
        )
        assert result.exit_code == 0

    def test_generate_with_content_class_photo(self):
        """Test generate with content class photo."""
        result = runner.invoke(
            app, ["generate", "a cat coding", "--use-mocks", "--style", "photo"]
        )
        assert result.exit_code == 0

    def test_generate_with_content_class_art(self):
        """Test generate with content class art."""
        result = runner.invoke(
            app, ["generate", "a cat coding", "--use-mocks", "--style", "art"]
        )
        assert result.exit_code == 0

    def test_generate_invalid_content_class(self):
        """Test generate with invalid content class."""
        result = runner.invoke(
            app, ["generate", "a cat coding", "--use-mocks", "--style", "invalid"]
        )
        assert result.exit_code == 1
        assert "--style must be either 'photo' or 'art'" in result.output

    def test_generate_invalid_variations_low(self):
        """Test generate with variations below minimum."""
        result = runner.invoke(
            app, ["generate", "a cat coding", "--use-mocks", "--variations", "0"]
        )
        assert result.exit_code == 1
        assert "--variations must be between 1 and 4" in result.output

    def test_generate_invalid_variations_high(self):
        """Test generate with variations above maximum."""
        result = runner.invoke(
            app, ["generate", "a cat coding", "--use-mocks", "--variations", "5"]
        )
        assert result.exit_code == 1
        assert "--variations must be between 1 and 4" in result.output

    def test_generate_with_negative_prompt(self):
        """Test generate with negative prompt."""
        result = runner.invoke(
            app, ["generate", "a cat coding", "--use-mocks", "--negative", "no text"]
        )
        assert result.exit_code == 0

    def test_generate_with_style_json(self):
        """Test generate with style JSON."""
        style_json = '{"presets": ["bw"], "strength": 50}'
        result = runner.invoke(
            app, ["generate", "a cat coding", "--use-mocks", "--style-json", style_json]
        )
        assert result.exit_code == 0

    def test_generate_invalid_style_json(self):
        """Test generate with invalid style JSON."""
        result = runner.invoke(
            app, ["generate", "a cat coding", "--use-mocks", "--style-json", "not-json"]
        )
        assert result.exit_code == 2
        assert "Invalid JSON for --style-json" in result.output

    def test_generate_with_structure_json(self):
        """Test generate with structure JSON."""
        structure_json = '{"strength": 80}'
        result = runner.invoke(
            app, ["generate", "a cat coding", "--use-mocks", "--structure-json", structure_json]
        )
        assert result.exit_code == 0

    def test_generate_invalid_structure_json(self):
        """Test generate with invalid structure JSON."""
        result = runner.invoke(
            app, ["generate", "a cat coding", "--use-mocks", "--structure-json", "not-json"]
        )
        assert result.exit_code == 2
        assert "Invalid JSON for --structure-json" in result.output

    def test_generate_with_locale(self):
        """Test generate with locale code."""
        result = runner.invoke(
            app, ["generate", "a cat coding", "--use-mocks", "--locale", "en-US"]
        )
        assert result.exit_code == 0

    def test_generate_with_output_format(self):
        """Test generate with output format."""
        result = runner.invoke(
            app, ["generate", "a cat coding", "--use-mocks", "--output-format", "png"]
        )
        assert result.exit_code == 0

    def test_generate_with_dimensions(self):
        """Test generate with custom dimensions."""
        result = runner.invoke(
            app, ["generate", "a cat coding", "--use-mocks", "--width", "512", "--height", "512"]
        )
        assert result.exit_code == 0

    def test_generate_with_download_mock(self):
        """Test generate with download flag in mock mode."""
        result = runner.invoke(
            app, ["generate", "a cat coding", "--use-mocks", "--download"]
        )
        assert result.exit_code == 0
        assert "[mock] Would download to:" in result.output

    def test_generate_with_show_images_mock(self):
        """Test generate with show-images flag in mock mode."""
        result = runner.invoke(
            app, ["generate", "a cat coding", "--use-mocks", "--show-images"]
        )
        assert result.exit_code == 0
        assert "[mock] Would display image in terminal" in result.output


class TestExpandCommand:
    """Tests for the expand command."""

    def test_expand_with_mocks(self):
        """Test expand command with mock API."""
        result = runner.invoke(
            app, ["expand", "https://example.com/image.jpg", "extend the sky", "--use-mocks"]
        )
        assert result.exit_code == 0
        assert "Expanded image URL:" in result.output
        assert MOCK_EXPAND_URL in result.output

    def test_expand_with_mocks_verbose(self):
        """Test expand with verbose output."""
        result = runner.invoke(
            app, ["expand", "https://example.com/image.jpg", "extend the sky", "--use-mocks", "--verbose"]
        )
        assert result.exit_code == 0
        assert "Using mock API responses" in result.output

    def test_expand_with_mocks_json_format(self):
        """Test expand with JSON output format."""
        result = runner.invoke(
            app, ["expand", "https://example.com/image.jpg", "extend the sky", "--use-mocks", "--format", "json"]
        )
        assert result.exit_code == 0
        assert "images" in result.output

    def test_expand_with_dimensions(self):
        """Test expand with target dimensions."""
        result = runner.invoke(
            app, ["expand", "https://example.com/image.jpg", "extend the sky", "--use-mocks", "--width", "2048", "--height", "1024"]
        )
        assert result.exit_code == 0

    def test_expand_with_alignment(self):
        """Test expand with alignment options."""
        result = runner.invoke(
            app, ["expand", "https://example.com/image.jpg", "extend the sky", "--use-mocks", "--h-align", "left", "--v-align", "top"]
        )
        assert result.exit_code == 0


class TestRemoveBgCommand:
    """Tests for the remove-bg command."""

    def test_remove_bg_with_mocks(self):
        """Test remove-bg command with mock API."""
        result = runner.invoke(
            app, ["remove-bg", "https://example.com/image.jpg", "--use-mocks"]
        )
        assert result.exit_code == 0
        assert "Result URL:" in result.output
        assert MOCK_CUTOUT_URL in result.output

    def test_remove_bg_with_mocks_verbose(self):
        """Test remove-bg with verbose output."""
        result = runner.invoke(
            app, ["remove-bg", "https://example.com/image.jpg", "--use-mocks", "--verbose"]
        )
        assert result.exit_code == 0
        assert "Using mock API responses" in result.output

    def test_remove_bg_with_mocks_json_format(self):
        """Test remove-bg with JSON output format."""
        result = runner.invoke(
            app, ["remove-bg", "https://example.com/image.jpg", "--use-mocks", "--format", "json"]
        )
        assert result.exit_code == 0
        assert "url" in result.output


class TestSimilarCommand:
    """Tests for the similar command."""

    def test_similar_with_mocks(self):
        """Test similar command with mock API."""
        result = runner.invoke(
            app, ["similar", "https://example.com/image.jpg", "--use-mocks"]
        )
        assert result.exit_code == 0
        assert "Similar image URL:" in result.output
        assert MOCK_SIMILAR_URL in result.output

    def test_similar_with_mocks_verbose(self):
        """Test similar with verbose output."""
        result = runner.invoke(
            app, ["similar", "https://example.com/image.jpg", "--use-mocks", "--verbose"]
        )
        assert result.exit_code == 0
        assert "Using mock API responses" in result.output

    def test_similar_with_mocks_json_format(self):
        """Test similar with JSON output format."""
        result = runner.invoke(
            app, ["similar", "https://example.com/image.jpg", "--use-mocks", "--format", "json"]
        )
        assert result.exit_code == 0
        assert "images" in result.output

    def test_similar_with_prompt(self):
        """Test similar with guiding prompt."""
        result = runner.invoke(
            app, ["similar", "https://example.com/image.jpg", "--use-mocks", "--prompt", "more colorful"]
        )
        assert result.exit_code == 0

    def test_similar_with_variations(self):
        """Test similar with multiple variations."""
        result = runner.invoke(
            app, ["similar", "https://example.com/image.jpg", "--use-mocks", "--variations", "3"]
        )
        assert result.exit_code == 0

    def test_similar_invalid_variations(self):
        """Test similar with invalid variations."""
        result = runner.invoke(
            app, ["similar", "https://example.com/image.jpg", "--use-mocks", "--variations", "5"]
        )
        assert result.exit_code == 1
        assert "--variations must be between 1 and 4" in result.output

    def test_similar_with_similarity(self):
        """Test similar with similarity parameter."""
        result = runner.invoke(
            app, ["similar", "https://example.com/image.jpg", "--use-mocks", "--similarity", "0.8"]
        )
        assert result.exit_code == 0


class TestStyleCommand:
    """Tests for the style command."""

    def test_style_with_mocks(self):
        """Test style command with mock API."""
        result = runner.invoke(
            app, ["style", "https://example.com/style.jpg", "a cityscape", "--use-mocks"]
        )
        assert result.exit_code == 0
        assert "Styled image URL:" in result.output
        assert MOCK_STYLE_URL in result.output

    def test_style_with_mocks_verbose(self):
        """Test style with verbose output."""
        result = runner.invoke(
            app, ["style", "https://example.com/style.jpg", "a cityscape", "--use-mocks", "--verbose"]
        )
        assert result.exit_code == 0
        assert "Using mock API responses" in result.output

    def test_style_with_mocks_json_format(self):
        """Test style with JSON output format."""
        result = runner.invoke(
            app, ["style", "https://example.com/style.jpg", "a cityscape", "--use-mocks", "--format", "json"]
        )
        assert result.exit_code == 0
        assert "images" in result.output

    def test_style_with_strength(self):
        """Test style with strength parameter."""
        result = runner.invoke(
            app, ["style", "https://example.com/style.jpg", "a cityscape", "--use-mocks", "--strength", "0.9"]
        )
        assert result.exit_code == 0


class TestVersionCommand:
    """Tests for the version command."""

    def test_version(self):
        """Test version command."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "firefly-sdk version" in result.output


class TestHelpOutput:
    """Tests for help output."""

    def test_main_help(self):
        """Test main help output."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Adobe Firefly CLI" in result.output

    def test_generate_help(self):
        """Test generate command help."""
        result = runner.invoke(app, ["generate", "--help"])
        assert result.exit_code == 0
        assert "Generate images" in result.output
        assert "--use-mocks" in result.output
        assert "--download" in result.output
        assert "--show-images" in result.output
        assert "--verbose" in result.output

    def test_expand_help(self):
        """Test expand command help."""
        result = runner.invoke(app, ["expand", "--help"])
        assert result.exit_code == 0
        assert "Expand an image" in result.output

    def test_remove_bg_help(self):
        """Test remove-bg command help."""
        result = runner.invoke(app, ["remove-bg", "--help"])
        assert result.exit_code == 0
        assert "Remove background" in result.output

    def test_similar_help(self):
        """Test similar command help."""
        result = runner.invoke(app, ["similar", "--help"])
        assert result.exit_code == 0
        assert "similar" in result.output.lower()

    def test_style_help(self):
        """Test style command help."""
        result = runner.invoke(app, ["style", "--help"])
        assert result.exit_code == 0
        assert "style" in result.output.lower()


class TestDownloadFunction:
    """Tests for the download_image function."""

    def test_download_image_mock(self):
        """Test download_image function with mock."""
        from firefly_sdk.cli import download_image
        from unittest.mock import patch, MagicMock
        import tempfile
        import os

        mock_response = MagicMock()
        mock_response.content = b"fake image data"

        with patch("firefly_sdk.cli.httpx.get", return_value=mock_response):
            with tempfile.TemporaryDirectory() as tmpdir:
                original_cwd = os.getcwd()
                os.chdir(tmpdir)
                try:
                    filename = download_image("https://example.com/test-image.png")
                    assert filename == "test-image.png"
                    assert os.path.exists(filename)
                    with open(filename, "rb") as f:
                        assert f.read() == b"fake image data"
                finally:
                    os.chdir(original_cwd)


class TestShowImageFunction:
    """Tests for the show_image_in_terminal function."""

    @mock.patch("subprocess.run")
    def test_show_image_url(self, mock_run):
        """Test showing image from URL."""
        from firefly_sdk.cli import show_image_in_terminal
        show_image_in_terminal("https://example.com/image.png")
        mock_run.assert_called_once_with(
            ["imgcat", "--url", "https://example.com/image.png"], check=True
        )

    @mock.patch("subprocess.run")
    def test_show_image_path(self, mock_run):
        """Test showing image from local path."""
        from firefly_sdk.cli import show_image_in_terminal
        show_image_in_terminal("/path/to/image.png")
        mock_run.assert_called_once_with(["imgcat", "/path/to/image.png"], check=True)

    @mock.patch("subprocess.run", side_effect=FileNotFoundError("imgcat not found"))
    def test_show_image_imgcat_not_found(self, mock_run, capsys):
        """Test handling when imgcat is not found."""
        from firefly_sdk.cli import show_image_in_terminal
        show_image_in_terminal("https://example.com/image.png")
        # Should not raise, just print warning
        captured = capsys.readouterr()
        assert "imgcat not found" in captured.err
