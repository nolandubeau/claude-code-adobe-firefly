#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "httpx>=0.27.0",
#   "python-dotenv>=1.0.0",
#   "rich>=13.7.0",
# ]
# ///
"""
02 - Background Removal with Adobe Firefly

This example demonstrates background removal using Adobe Firefly.
Run with: uv run apps/firefly_examples/02_remove_background.py <image_url>
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


async def remove_background(image_url: str) -> dict:
    """Remove background from an image."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        with console.status("Authenticating..."):
            token = await get_access_token(client)

        with console.status("Removing background..."):
            response = await client.post(
                f"{API_BASE}/v2/images/cutout",
                json={
                    "image": {"source": {"url": image_url}},
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
    if len(sys.argv) < 2:
        console.print("[yellow]Usage: uv run 02_remove_background.py <image_url>[/yellow]")
        console.print("\nExample:")
        console.print("  uv run 02_remove_background.py https://example.com/photo.jpg")
        sys.exit(1)

    image_url = sys.argv[1]

    console.print(f"\n[bold blue]Adobe Firefly Background Removal[/bold blue]")
    console.print(f"[dim]Input: {image_url}[/dim]\n")

    result = await remove_background(image_url)

    console.print("[green]✓ Background removed successfully![/green]\n")
    console.print(f"[cyan]Result URL:[/cyan] {result['output']['url']}")


if __name__ == "__main__":
    asyncio.run(main())
