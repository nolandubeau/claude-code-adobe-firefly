#!/usr/bin/env python3
"""
Adobe Firefly CLI - Command line interface for Firefly API.
"""

import asyncio
import json
import click
from rich.console import Console
from rich.table import Table

from firefly_sdk.client import FireflyClient, FireflyAuthError, FireflyAPIError
from firefly_sdk.models import (
    GenerateImageRequest,
    ExpandImageRequest,
    FillImageRequest,
    RemoveBackgroundRequest,
    GenerateSimilarRequest,
    StyleTransferRequest,
)

console = Console()


def run_async(coro):
    """Run an async function synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


@click.group()
@click.version_option(version="1.0.0")
def main():
    """Adobe Firefly CLI - AI-powered image generation and editing."""
    pass


@main.command()
@click.argument("prompt")
@click.option("--width", "-w", default=1024, help="Image width")
@click.option("--height", "-h", default=1024, help="Image height")
@click.option("--variations", "-n", default=1, help="Number of variations (1-4)")
@click.option("--style", "-s", default=None, help="Content class: photo or art")
@click.option("--negative", default=None, help="Negative prompt")
@click.option("--json-output", is_flag=True, help="Output as JSON")
def generate(prompt, width, height, variations, style, negative, json_output):
    """Generate images from a text prompt."""
    async def _generate():
        try:
            async with FireflyClient() as client:
                request = GenerateImageRequest(
                    prompt=prompt,
                    width=width,
                    height=height,
                    num_variations=variations,
                    content_class=style,
                    negative_prompt=negative,
                )

                with console.status("Generating images..."):
                    response = await client.generate_image(request)

                if json_output:
                    click.echo(json.dumps(
                        {"images": [img.model_dump() for img in response.images]},
                        indent=2
                    ))
                else:
                    table = Table(title="Generated Images")
                    table.add_column("Index", style="cyan")
                    table.add_column("URL", style="green")
                    table.add_column("Seed", style="yellow")

                    for i, img in enumerate(response.images):
                        table.add_row(str(i + 1), img.url, str(img.seed or "N/A"))

                    console.print(table)

        except FireflyAuthError as e:
            console.print(f"[red]Authentication error:[/red] {e}")
            raise SystemExit(1)
        except FireflyAPIError as e:
            console.print(f"[red]API error ({e.status_code}):[/red] {e}")
            raise SystemExit(1)

    run_async(_generate())


@main.command()
@click.argument("image_url")
@click.argument("prompt")
@click.option("--width", "-w", default=None, type=int, help="Target width")
@click.option("--height", "-h", default=None, type=int, help="Target height")
@click.option("--h-align", default="center", help="Horizontal alignment: left, center, right")
@click.option("--v-align", default="center", help="Vertical alignment: top, center, bottom")
@click.option("--json-output", is_flag=True, help="Output as JSON")
def expand(image_url, prompt, width, height, h_align, v_align, json_output):
    """Expand an image beyond its boundaries."""
    async def _expand():
        try:
            async with FireflyClient() as client:
                from firefly_sdk.models import Placement

                request = ExpandImageRequest(
                    image_url=image_url,
                    prompt=prompt,
                    target_width=width,
                    target_height=height,
                    placement=Placement(horizontal_align=h_align, vertical_align=v_align),
                )

                with console.status("Expanding image..."):
                    response = await client.expand_image(request)

                if json_output:
                    click.echo(json.dumps(
                        {"images": [img.model_dump() for img in response.images]},
                        indent=2
                    ))
                else:
                    for i, img in enumerate(response.images):
                        console.print(f"[green]Expanded image {i + 1}:[/green] {img.url}")

        except FireflyAuthError as e:
            console.print(f"[red]Authentication error:[/red] {e}")
            raise SystemExit(1)
        except FireflyAPIError as e:
            console.print(f"[red]API error ({e.status_code}):[/red] {e}")
            raise SystemExit(1)

    run_async(_expand())


@main.command("remove-bg")
@click.argument("image_url")
@click.option("--json-output", is_flag=True, help="Output as JSON")
def remove_bg(image_url, json_output):
    """Remove background from an image."""
    async def _remove_bg():
        try:
            async with FireflyClient() as client:
                request = RemoveBackgroundRequest(image_url=image_url)

                with console.status("Removing background..."):
                    response = await client.remove_background(request)

                if json_output:
                    click.echo(json.dumps({"url": response.url}, indent=2))
                else:
                    console.print(f"[green]Result:[/green] {response.url}")

        except FireflyAuthError as e:
            console.print(f"[red]Authentication error:[/red] {e}")
            raise SystemExit(1)
        except FireflyAPIError as e:
            console.print(f"[red]API error ({e.status_code}):[/red] {e}")
            raise SystemExit(1)

    run_async(_remove_bg())


@main.command()
@click.argument("reference_url")
@click.option("--prompt", "-p", default=None, help="Guiding prompt")
@click.option("--variations", "-n", default=1, help="Number of variations (1-4)")
@click.option("--similarity", default=0.5, help="Similarity to reference (0-1)")
@click.option("--json-output", is_flag=True, help="Output as JSON")
def similar(reference_url, prompt, variations, similarity, json_output):
    """Generate images similar to a reference."""
    async def _similar():
        try:
            async with FireflyClient() as client:
                request = GenerateSimilarRequest(
                    reference_image_url=reference_url,
                    prompt=prompt,
                    num_variations=variations,
                    similarity=similarity,
                )

                with console.status("Generating similar images..."):
                    response = await client.generate_similar(request)

                if json_output:
                    click.echo(json.dumps(
                        {"images": [img.model_dump() for img in response.images]},
                        indent=2
                    ))
                else:
                    table = Table(title="Similar Images")
                    table.add_column("Index", style="cyan")
                    table.add_column("URL", style="green")

                    for i, img in enumerate(response.images):
                        table.add_row(str(i + 1), img.url)

                    console.print(table)

        except FireflyAuthError as e:
            console.print(f"[red]Authentication error:[/red] {e}")
            raise SystemExit(1)
        except FireflyAPIError as e:
            console.print(f"[red]API error ({e.status_code}):[/red] {e}")
            raise SystemExit(1)

    run_async(_similar())


@main.command()
@click.argument("style_url")
@click.argument("prompt")
@click.option("--strength", default=0.7, help="Style strength (0-1)")
@click.option("--json-output", is_flag=True, help="Output as JSON")
def style(style_url, prompt, strength, json_output):
    """Apply style from a reference image."""
    async def _style():
        try:
            async with FireflyClient() as client:
                request = StyleTransferRequest(
                    style_image_url=style_url,
                    prompt=prompt,
                    style_strength=strength,
                )

                with console.status("Applying style..."):
                    response = await client.apply_style_transfer(request)

                if json_output:
                    click.echo(json.dumps(
                        {"images": [img.model_dump() for img in response.images]},
                        indent=2
                    ))
                else:
                    for i, img in enumerate(response.images):
                        console.print(f"[green]Styled image {i + 1}:[/green] {img.url}")

        except FireflyAuthError as e:
            console.print(f"[red]Authentication error:[/red] {e}")
            raise SystemExit(1)
        except FireflyAPIError as e:
            console.print(f"[red]API error ({e.status_code}):[/red] {e}")
            raise SystemExit(1)

    run_async(_style())


if __name__ == "__main__":
    main()
