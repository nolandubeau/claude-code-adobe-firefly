#!/usr/bin/env python3
"""
Adobe Firefly CLI - Command line interface for Firefly API.

Features:
- Generate images from text prompts
- Expand images beyond boundaries
- Remove backgrounds
- Generate similar images
- Apply style transfer
- Mock mode for testing without API credentials
- Download and display images
"""

import asyncio
import json
import os
import subprocess
import sys
from typing import Optional
from urllib.parse import urlparse

import httpx
import typer
from rich.console import Console
from rich.table import Table

from firefly_sdk.client import FireflyClient, FireflyAuthError, FireflyAPIError
from firefly_sdk.models import (
    GenerateImageRequest,
    ExpandImageRequest,
    RemoveBackgroundRequest,
    GenerateSimilarRequest,
    StyleTransferRequest,
    Placement,
)

# Initialize Typer app
app = typer.Typer(
    name="firefly",
    help="Adobe Firefly CLI - AI-powered image generation and editing.",
    add_completion=False,
)

console = Console()

# Global state for mock mode
_use_mocks = False


def run_async(coro):
    """Run an async function synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


def download_image(url: str, filename: Optional[str] = None) -> str:
    """Download image from URL to local file."""
    response = httpx.get(url, follow_redirects=True)
    response.raise_for_status()

    if not filename:
        path = urlparse(url).path
        filename = os.path.basename(path) or "firefly-image.png"

    with open(filename, "wb") as f:
        f.write(response.content)

    size = len(response.content)
    typer.echo(f"Downloaded image ({size} bytes) to {filename}")
    return filename


def show_image_in_terminal(url_or_path: str):
    """Display image in terminal using imgcat (iTerm2) or similar."""
    try:
        if url_or_path.startswith("http"):
            subprocess.run(["imgcat", "--url", url_or_path], check=True)
        else:
            subprocess.run(["imgcat", url_or_path], check=True)
    except FileNotFoundError:
        typer.secho(
            "[warn] imgcat not found. Install with: brew install imgcat",
            fg=typer.colors.YELLOW,
            err=True,
        )
    except subprocess.CalledProcessError as e:
        typer.secho(
            f"[warn] Could not display image: {e}",
            fg=typer.colors.YELLOW,
            err=True,
        )


def get_client(use_mocks: bool = False) -> FireflyClient:
    """Get Firefly client, optionally in mock mode."""
    if use_mocks:
        from firefly_sdk.mocks import use_sync_firefly_mocks
        # In mock mode, we'll handle this differently in each command
        pass

    return FireflyClient()


@app.command()
def generate(
    prompt: str = typer.Argument(..., help="Text prompt for image generation"),
    width: int = typer.Option(1024, "--width", "-w", help="Image width in pixels"),
    height: int = typer.Option(1024, "--height", "-h", help="Image height in pixels"),
    variations: int = typer.Option(1, "--variations", "-n", help="Number of variations (1-4)"),
    content_class: Optional[str] = typer.Option(None, "--style", "-s", help="Content class: photo or art"),
    negative: Optional[str] = typer.Option(None, "--negative", help="Negative prompt"),
    seed: Optional[int] = typer.Option(None, "--seed", help="Seed for deterministic output"),
    aspect_ratio: Optional[str] = typer.Option(None, "--aspect-ratio", help="Aspect ratio e.g. '16:9'"),
    output_format: Optional[str] = typer.Option(None, "--output-format", help="Output format: jpeg or png"),
    locale: Optional[str] = typer.Option(None, "--locale", help="Locale code e.g. 'en-US'"),
    style_json: Optional[str] = typer.Option(None, "--style-json", help="Style object as JSON string"),
    structure_json: Optional[str] = typer.Option(None, "--structure-json", help="Structure object as JSON string"),
    download: bool = typer.Option(False, "--download", help="Download generated image to file"),
    show_images: bool = typer.Option(False, "--show-images", help="Display image in terminal"),
    use_mocks: bool = typer.Option(False, "--use-mocks", help="Use mock API for testing"),
    format_output: str = typer.Option("text", "--format", help="Output format: text or json"),
    verbose: bool = typer.Option(False, "--verbose", help="Print verbose status messages"),
):
    """Generate images from a text prompt using Adobe Firefly API."""

    # Validate content_class
    if content_class and content_class not in ("photo", "art"):
        typer.secho("--style must be either 'photo' or 'art'", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    # Validate variations
    if not (1 <= variations <= 4):
        typer.secho("--variations must be between 1 and 4", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    # Parse JSON options
    style_options = None
    if style_json:
        try:
            style_options = json.loads(style_json)
        except json.JSONDecodeError as e:
            typer.secho(f"Invalid JSON for --style-json: {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=2)

    structure = None
    if structure_json:
        try:
            structure = json.loads(structure_json)
        except json.JSONDecodeError as e:
            typer.secho(f"Invalid JSON for --structure-json: {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=2)

    async def _generate():
        if use_mocks:
            from firefly_sdk.mocks import use_sync_firefly_mocks, MOCK_GENERATE_RESPONSE, MOCK_IMAGE_URL
            if verbose:
                typer.secho("Using mock API responses", fg=typer.colors.YELLOW, err=True)

            # Return mock response
            if format_output == "json":
                console.print_json(data=MOCK_GENERATE_RESPONSE)
            else:
                typer.echo(f"Generated image URL: {MOCK_IMAGE_URL}")
                typer.echo(f"Seed: 123456")
                if download:
                    typer.echo(f"[mock] Would download to: firefly-image.png")
                if show_images:
                    typer.echo(f"[mock] Would display image in terminal")
            return

        try:
            if verbose:
                typer.secho(f"Generating image with prompt: {prompt[:50]}...", fg=typer.colors.YELLOW, err=True)

            async with FireflyClient() as client:
                request = GenerateImageRequest(
                    prompt=prompt,
                    width=width,
                    height=height,
                    num_variations=variations,
                    content_class=content_class,
                    negative_prompt=negative,
                    seed=seed,
                    aspect_ratio=aspect_ratio,
                    output_format=output_format,
                    prompt_biasing_locale_code=locale,
                    style_options=style_options,
                    structure=structure,
                )

                if verbose:
                    typer.secho("Sending request to Firefly API...", fg=typer.colors.YELLOW, err=True)

                response = await client.generate_image(request)

                if verbose:
                    typer.secho(f"Received {len(response.images)} image(s)", fg=typer.colors.YELLOW, err=True)

            if format_output == "json":
                console.print_json(data={
                    "images": [img.model_dump() for img in response.images],
                    "content_class": response.content_class,
                })
            else:
                for i, img in enumerate(response.images):
                    typer.echo(f"Generated image URL: {img.url}")
                    if img.seed:
                        typer.echo(f"Seed: {img.seed}")

                    if download:
                        download_image(img.url)

                    if show_images:
                        show_image_in_terminal(img.url)

        except FireflyAuthError as e:
            typer.secho(f"Authentication error: {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        except FireflyAPIError as e:
            typer.secho(f"API error ({e.status_code}): {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)

    run_async(_generate())


@app.command()
def expand(
    image_url: str = typer.Argument(..., help="URL of image to expand"),
    prompt: str = typer.Argument(..., help="Description of expanded content"),
    width: Optional[int] = typer.Option(None, "--width", "-w", help="Target width"),
    height: Optional[int] = typer.Option(None, "--height", "-h", help="Target height"),
    h_align: str = typer.Option("center", "--h-align", help="Horizontal alignment: left, center, right"),
    v_align: str = typer.Option("center", "--v-align", help="Vertical alignment: top, center, bottom"),
    download: bool = typer.Option(False, "--download", help="Download result to file"),
    show_images: bool = typer.Option(False, "--show-images", help="Display in terminal"),
    use_mocks: bool = typer.Option(False, "--use-mocks", help="Use mock API for testing"),
    format_output: str = typer.Option("text", "--format", help="Output format: text or json"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose output"),
):
    """Expand an image beyond its boundaries."""

    async def _expand():
        if use_mocks:
            from firefly_sdk.mocks import MOCK_EXPAND_RESPONSE, MOCK_EXPAND_URL
            if verbose:
                typer.secho("Using mock API responses", fg=typer.colors.YELLOW, err=True)
            if format_output == "json":
                console.print_json(data=MOCK_EXPAND_RESPONSE)
            else:
                typer.echo(f"Expanded image URL: {MOCK_EXPAND_URL}")
            return

        try:
            async with FireflyClient() as client:
                request = ExpandImageRequest(
                    image_url=image_url,
                    prompt=prompt,
                    target_width=width,
                    target_height=height,
                    placement=Placement(horizontal_align=h_align, vertical_align=v_align),
                )

                if verbose:
                    typer.secho("Expanding image...", fg=typer.colors.YELLOW, err=True)

                response = await client.expand_image(request)

            if format_output == "json":
                console.print_json(data={"images": [img.model_dump() for img in response.images]})
            else:
                for img in response.images:
                    typer.echo(f"Expanded image URL: {img.url}")
                    if download:
                        download_image(img.url)
                    if show_images:
                        show_image_in_terminal(img.url)

        except FireflyAuthError as e:
            typer.secho(f"Authentication error: {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        except FireflyAPIError as e:
            typer.secho(f"API error ({e.status_code}): {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)

    run_async(_expand())


@app.command("remove-bg")
def remove_bg(
    image_url: str = typer.Argument(..., help="URL of image to process"),
    download: bool = typer.Option(False, "--download", help="Download result to file"),
    show_images: bool = typer.Option(False, "--show-images", help="Display in terminal"),
    use_mocks: bool = typer.Option(False, "--use-mocks", help="Use mock API for testing"),
    format_output: str = typer.Option("text", "--format", help="Output format: text or json"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose output"),
):
    """Remove background from an image."""

    async def _remove_bg():
        if use_mocks:
            from firefly_sdk.mocks import MOCK_CUTOUT_RESPONSE, MOCK_CUTOUT_URL
            if verbose:
                typer.secho("Using mock API responses", fg=typer.colors.YELLOW, err=True)
            if format_output == "json":
                console.print_json(data={"url": MOCK_CUTOUT_URL})
            else:
                typer.echo(f"Result URL: {MOCK_CUTOUT_URL}")
            return

        try:
            async with FireflyClient() as client:
                request = RemoveBackgroundRequest(image_url=image_url)

                if verbose:
                    typer.secho("Removing background...", fg=typer.colors.YELLOW, err=True)

                response = await client.remove_background(request)

            if format_output == "json":
                console.print_json(data={"url": response.url})
            else:
                typer.echo(f"Result URL: {response.url}")
                if download:
                    download_image(response.url)
                if show_images:
                    show_image_in_terminal(response.url)

        except FireflyAuthError as e:
            typer.secho(f"Authentication error: {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        except FireflyAPIError as e:
            typer.secho(f"API error ({e.status_code}): {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)

    run_async(_remove_bg())


@app.command()
def similar(
    reference_url: str = typer.Argument(..., help="URL of reference image"),
    prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="Guiding prompt"),
    variations: int = typer.Option(1, "--variations", "-n", help="Number of variations (1-4)"),
    similarity: float = typer.Option(0.5, "--similarity", help="Similarity to reference (0-1)"),
    download: bool = typer.Option(False, "--download", help="Download results to files"),
    show_images: bool = typer.Option(False, "--show-images", help="Display in terminal"),
    use_mocks: bool = typer.Option(False, "--use-mocks", help="Use mock API for testing"),
    format_output: str = typer.Option("text", "--format", help="Output format: text or json"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose output"),
):
    """Generate images similar to a reference."""

    if not (1 <= variations <= 4):
        typer.secho("--variations must be between 1 and 4", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    async def _similar():
        if use_mocks:
            from firefly_sdk.mocks import MOCK_SIMILAR_RESPONSE, MOCK_SIMILAR_URL
            if verbose:
                typer.secho("Using mock API responses", fg=typer.colors.YELLOW, err=True)
            if format_output == "json":
                console.print_json(data=MOCK_SIMILAR_RESPONSE)
            else:
                typer.echo(f"Similar image URL: {MOCK_SIMILAR_URL}")
            return

        try:
            async with FireflyClient() as client:
                request = GenerateSimilarRequest(
                    reference_image_url=reference_url,
                    prompt=prompt,
                    num_variations=variations,
                    similarity=similarity,
                )

                if verbose:
                    typer.secho("Generating similar images...", fg=typer.colors.YELLOW, err=True)

                response = await client.generate_similar(request)

            if format_output == "json":
                console.print_json(data={"images": [img.model_dump() for img in response.images]})
            else:
                table = Table(title="Similar Images")
                table.add_column("Index", style="cyan")
                table.add_column("URL", style="green")

                for i, img in enumerate(response.images):
                    table.add_row(str(i + 1), img.url)
                    if download:
                        download_image(img.url)
                    if show_images:
                        show_image_in_terminal(img.url)

                console.print(table)

        except FireflyAuthError as e:
            typer.secho(f"Authentication error: {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        except FireflyAPIError as e:
            typer.secho(f"API error ({e.status_code}): {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)

    run_async(_similar())


@app.command()
def style(
    style_url: str = typer.Argument(..., help="URL of style reference image"),
    prompt: str = typer.Argument(..., help="Content to generate with style"),
    strength: float = typer.Option(0.7, "--strength", help="Style strength (0-1)"),
    download: bool = typer.Option(False, "--download", help="Download result to file"),
    show_images: bool = typer.Option(False, "--show-images", help="Display in terminal"),
    use_mocks: bool = typer.Option(False, "--use-mocks", help="Use mock API for testing"),
    format_output: str = typer.Option("text", "--format", help="Output format: text or json"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose output"),
):
    """Apply style from a reference image to new content."""

    async def _style():
        if use_mocks:
            from firefly_sdk.mocks import MOCK_STYLE_RESPONSE, MOCK_STYLE_URL
            if verbose:
                typer.secho("Using mock API responses", fg=typer.colors.YELLOW, err=True)
            if format_output == "json":
                console.print_json(data=MOCK_STYLE_RESPONSE)
            else:
                typer.echo(f"Styled image URL: {MOCK_STYLE_URL}")
            return

        try:
            async with FireflyClient() as client:
                request = StyleTransferRequest(
                    style_image_url=style_url,
                    prompt=prompt,
                    style_strength=strength,
                )

                if verbose:
                    typer.secho("Applying style transfer...", fg=typer.colors.YELLOW, err=True)

                response = await client.apply_style_transfer(request)

            if format_output == "json":
                console.print_json(data={"images": [img.model_dump() for img in response.images]})
            else:
                for img in response.images:
                    typer.echo(f"Styled image URL: {img.url}")
                    if download:
                        download_image(img.url)
                    if show_images:
                        show_image_in_terminal(img.url)

        except FireflyAuthError as e:
            typer.secho(f"Authentication error: {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        except FireflyAPIError as e:
            typer.secho(f"API error ({e.status_code}): {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)

    run_async(_style())


@app.command()
def version():
    """Show version information."""
    typer.echo("firefly-sdk version 1.0.0")


if __name__ == "__main__":
    app()
