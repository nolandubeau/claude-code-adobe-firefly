#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "httpx>=0.27.0",
#   "python-dotenv>=1.0.0",
#   "rich>=13.7.0",
# ]
# ///
"""
04 - Style Transfer with Adobe Firefly

This example demonstrates applying an artistic style from a reference image.
Run with: uv run apps/firefly_examples/04_style_transfer.py <style_url> "<prompt>"
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


async def apply_style_transfer(
    style_url: str,
    prompt: str,
    style_strength: float = 0.7,
) -> dict:
    """Apply style from a reference image to new content."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        with console.status("Authenticating..."):
            token = await get_access_token(client)

        with console.status("Applying style transfer..."):
            response = await client.post(
                f"{API_BASE}/v3/images/generate",
                json={
                    "prompt": prompt,
                    "n": 1,
                    "size": {"width": 1024, "height": 1024},
                    "style": {
                        "imageReference": {"source": {"url": style_url}},
                        "strength": style_strength,
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
        console.print("[yellow]Usage: uv run 04_style_transfer.py <style_url> \"<prompt>\" [strength][/yellow]")
        console.print("\nExample:")
        console.print('  uv run 04_style_transfer.py https://example.com/vangogh.jpg "a city street" 0.8')
        sys.exit(1)

    style_url = sys.argv[1]
    prompt = sys.argv[2]
    strength = float(sys.argv[3]) if len(sys.argv) > 3 else 0.7

    console.print(f"\n[bold blue]Adobe Firefly Style Transfer[/bold blue]")
    console.print(f"[dim]Style: {style_url}[/dim]")
    console.print(f"[dim]Prompt: {prompt}[/dim]")
    console.print(f"[dim]Strength: {strength}[/dim]\n")

    result = await apply_style_transfer(style_url, prompt, strength)

    console.print("[green]✓ Style transfer complete![/green]\n")

    for i, image in enumerate(result.get("images", [])):
        console.print(f"[cyan]Styled image {i + 1}:[/cyan] {image['url']}")


if __name__ == "__main__":
    asyncio.run(main())
