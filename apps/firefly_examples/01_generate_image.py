#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "httpx>=0.27.0",
#   "python-dotenv>=1.0.0",
#   "rich>=13.7.0",
# ]
# ///
"""
01 - Basic Image Generation with Adobe Firefly

This example demonstrates basic image generation using the Adobe Firefly API.
Run with: uv run apps/firefly_examples/01_generate_image.py
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
import httpx
from rich.console import Console

load_dotenv()

console = Console()

# Configuration
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


async def generate_image(prompt: str, content_class: str = "photo") -> dict:
    """Generate an image from a text prompt."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Get access token
        with console.status("Authenticating..."):
            token = await get_access_token(client)

        # Generate image
        with console.status("Generating image..."):
            response = await client.post(
                f"{API_BASE}/v3/images/generate",
                json={
                    "prompt": prompt,
                    "n": 1,
                    "size": {"width": 1024, "height": 1024},
                    "contentClass": content_class,
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "x-api-key": os.getenv("FIREFLY_CLIENT_ID"),
                    "Content-Type": "application/json",
                },
            )

        if response.status_code != 200:
            console.print(f"[red]Generation failed: {response.text}[/red]")
            sys.exit(1)

        return response.json()


async def main():
    # Default prompt or from command line
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else \
        "A serene mountain landscape at golden hour with dramatic clouds"

    console.print(f"\n[bold blue]Adobe Firefly Image Generation[/bold blue]")
    console.print(f"[dim]Prompt: {prompt}[/dim]\n")

    result = await generate_image(prompt)

    console.print("[green]✓ Image generated successfully![/green]\n")

    for i, image in enumerate(result.get("images", [])):
        console.print(f"[cyan]Image {i + 1}:[/cyan]")
        console.print(f"  URL: {image['url']}")
        if image.get("seed"):
            console.print(f"  Seed: {image['seed']}")
        console.print()


if __name__ == "__main__":
    asyncio.run(main())
