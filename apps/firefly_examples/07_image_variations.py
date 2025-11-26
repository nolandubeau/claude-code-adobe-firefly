#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "httpx>=0.27.0",
#   "python-dotenv>=1.0.0",
#   "rich>=13.7.0",
# ]
# ///
"""
07 - Image Variations with Adobe Firefly

This example demonstrates generating multiple variations of an image
with different parameters to explore creative directions.

Run with: uv run apps/firefly_examples/07_image_variations.py "<prompt>"
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns

load_dotenv()

console = Console()

AUTH_URL = "https://ims-na1.adobelogin.com/ims/token/v3"
API_BASE = "https://firefly-api.adobe.io"
SCOPES = "openid,AdobeID,firefly_api,ff_apis"


async def get_access_token(client: httpx.AsyncClient) -> str:
    """Authenticate and get access token."""
    client_id = os.getenv("FIREFLY_CLIENT_ID")
    client_secret = os.getenv("FIREFLY_CLIENT_SECRET")

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
        raise Exception(f"Auth failed: {response.text}")

    return response.json()["access_token"]


async def generate_variation(
    client: httpx.AsyncClient,
    token: str,
    prompt: str,
    content_class: str,
    size: dict,
    variation_id: int,
) -> dict:
    """Generate a single variation with specific parameters."""
    response = await client.post(
        f"{API_BASE}/v3/images/generate",
        json={
            "prompt": prompt,
            "n": 1,
            "size": size,
            "contentClass": content_class,
        },
        headers={
            "Authorization": f"Bearer {token}",
            "x-api-key": os.getenv("FIREFLY_CLIENT_ID"),
            "Content-Type": "application/json",
        },
    )

    if response.status_code != 200:
        return {
            "variation_id": variation_id,
            "success": False,
            "error": response.text,
            "content_class": content_class,
            "size": size,
        }

    result = response.json()
    images = result.get("images", [])

    return {
        "variation_id": variation_id,
        "success": True,
        "url": images[0]["url"] if images else None,
        "seed": images[0].get("seed") if images else None,
        "content_class": content_class,
        "size": size,
    }


async def generate_variations(prompt: str) -> list[dict]:
    """Generate multiple variations with different parameters."""
    # Define variation parameters
    variations = [
        # Different content classes
        {"content_class": "photo", "size": {"width": 1024, "height": 1024}},
        {"content_class": "art", "size": {"width": 1024, "height": 1024}},
        # Different aspect ratios
        {"content_class": "photo", "size": {"width": 1920, "height": 1080}},  # 16:9
        {"content_class": "photo", "size": {"width": 1080, "height": 1920}},  # 9:16
        {"content_class": "art", "size": {"width": 1024, "height": 768}},     # 4:3
        {"content_class": "art", "size": {"width": 768, "height": 1024}},     # 3:4
    ]

    async with httpx.AsyncClient(timeout=60.0) as client:
        with console.status("Authenticating..."):
            token = await get_access_token(client)

        console.print("[cyan]Generating variations...[/cyan]\n")

        tasks = [
            generate_variation(
                client, token, prompt,
                var["content_class"], var["size"], i + 1
            )
            for i, var in enumerate(variations)
        ]

        results = await asyncio.gather(*tasks)

    return results


def display_results(results: list[dict], prompt: str):
    """Display results in a formatted layout."""
    console.print(Panel.fit(f"[bold]Prompt:[/bold] {prompt}", title="Variation Results"))
    console.print()

    panels = []
    for result in results:
        if result["success"]:
            size = result["size"]
            content = f"""[green]Success[/green]
[dim]Class:[/dim] {result['content_class']}
[dim]Size:[/dim] {size['width']}x{size['height']}
[dim]Seed:[/dim] {result.get('seed', 'N/A')}
[dim]URL:[/dim] {result['url'][:40]}..."""
        else:
            content = f"[red]Failed[/red]\n{result.get('error', 'Unknown error')[:50]}"

        panels.append(Panel(content, title=f"Variation {result['variation_id']}"))

    # Display in columns
    for i in range(0, len(panels), 2):
        row = panels[i:i+2]
        console.print(Columns(row, equal=True))
        console.print()


async def main():
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else \
        "A majestic mountain peak at golden hour"

    console.print("\n[bold blue]Adobe Firefly Image Variations[/bold blue]\n")

    results = await generate_variations(prompt)
    display_results(results, prompt)

    success_count = sum(1 for r in results if r["success"])
    console.print(f"[bold]Generated {success_count}/{len(results)} variations successfully[/bold]")


if __name__ == "__main__":
    asyncio.run(main())
