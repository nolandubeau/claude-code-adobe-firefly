#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "httpx>=0.27.0",
#   "python-dotenv>=1.0.0",
#   "rich>=13.7.0",
# ]
# ///
"""
03 - Image Expansion (Outpainting) with Adobe Firefly

This example demonstrates generative expand to extend images beyond boundaries.
Run with: uv run apps/firefly_examples/03_expand_image.py <image_url> "<prompt>"
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
import httpx
from rich.console import Console

load_dotenv()

console = Console()

AUTH_URL = "https://ims-na1.adobelogin.com/ims/token/v3"
API_BASE = "https://firefly-api.adobe.io"
SCOPES = "openid,AdobeID,firefly_api,ff_apis"


async def get_access_token(client: httpx.AsyncClient) -> str:
    """Authenticate and get access token."""
    client_id = os.getenv("FIREFLY_CLIENT_ID")
    client_secret = os.getenv("FIREFLY_CLIENT_SECRET")

    if not client_id or not client_secret:
        console.print("[red]Error: Set FIREFLY_CLIENT_ID and FIREFLY_CLIENT_SECRET[/red]")
        sys.exit(1)

    response = await client.post(
        AUTH_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": SCOPES,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if response.status_code != 200:
        console.print(f"[red]Auth failed: {response.text}[/red]")
        sys.exit(1)

    return response.json()["access_token"]


async def expand_image(
    image_url: str,
    prompt: str,
    target_width: int = 2048,
    target_height: int = 1024,
) -> dict:
    """Expand an image beyond its boundaries."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        with console.status("Authenticating..."):
            token = await get_access_token(client)

        with console.status("Expanding image..."):
            response = await client.post(
                f"{API_BASE}/v3/images/expand",
                json={
                    "image": {"source": {"url": image_url}},
                    "prompt": prompt,
                    "size": {
                        "width": target_width,
                        "height": target_height,
                    },
                    "placement": {
                        "alignment": {
                            "horizontal": "center",
                            "vertical": "center",
                        }
                    },
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "x-api-key": os.getenv("FIREFLY_CLIENT_ID"),
                    "Content-Type": "application/json",
                },
            )

        if response.status_code != 200:
            console.print(f"[red]Operation failed: {response.text}[/red]")
            sys.exit(1)

        return response.json()


async def main():
    if len(sys.argv) < 3:
        console.print("[yellow]Usage: uv run 03_expand_image.py <image_url> \"<prompt>\"[/yellow]")
        console.print("\nExample:")
        console.print('  uv run 03_expand_image.py https://example.com/photo.jpg "continue the landscape"')
        sys.exit(1)

    image_url = sys.argv[1]
    prompt = sys.argv[2]

    console.print(f"\n[bold blue]Adobe Firefly Image Expansion[/bold blue]")
    console.print(f"[dim]Input: {image_url}[/dim]")
    console.print(f"[dim]Prompt: {prompt}[/dim]\n")

    result = await expand_image(image_url, prompt)

    console.print("[green]✓ Image expanded successfully![/green]\n")

    for i, image in enumerate(result.get("images", [])):
        console.print(f"[cyan]Expanded image {i + 1}:[/cyan] {image['url']}")


if __name__ == "__main__":
    asyncio.run(main())
