#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "httpx>=0.27.0",
#   "python-dotenv>=1.0.0",
#   "rich>=13.7.0",
# ]
# ///
"""
06 - Batch Processing with Adobe Firefly

This example demonstrates batch processing multiple images in parallel
using asyncio for efficient execution.

Run with: uv run apps/firefly_examples/06_batch_processing.py
"""

import asyncio
import os
import sys
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv
import httpx
from rich.console import Console
from rich.progress import Progress, TaskID
from rich.table import Table

load_dotenv()

console = Console()

AUTH_URL = "https://ims-na1.adobelogin.com/ims/token/v3"
API_BASE = "https://firefly-api.adobe.io"
SCOPES = "openid,AdobeID,firefly_api,ff_apis"


@dataclass
class BatchResult:
    """Result of a batch operation."""
    prompt: str
    success: bool
    url: Optional[str] = None
    error: Optional[str] = None
    duration: float = 0.0


class BatchProcessor:
    """Process multiple Firefly API requests in parallel."""

    def __init__(self, max_concurrent: int = 3):
        self.client_id = os.getenv("FIREFLY_CLIENT_ID")
        self.client_secret = os.getenv("FIREFLY_CLIENT_SECRET")
        self._token: Optional[str] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def __aenter__(self):
        self._http_client = httpx.AsyncClient(timeout=60.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._http_client:
            await self._http_client.aclose()

    async def _authenticate(self) -> str:
        if self._token:
            return self._token

        response = await self._http_client.post(
            AUTH_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": SCOPES,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code != 200:
            raise Exception(f"Auth failed: {response.text}")

        self._token = response.json()["access_token"]
        return self._token

    async def generate_image(
        self,
        prompt: str,
        progress: Progress,
        task_id: TaskID,
    ) -> BatchResult:
        """Generate a single image with rate limiting."""
        import time
        start_time = time.time()

        async with self._semaphore:
            try:
                token = await self._authenticate()

                response = await self._http_client.post(
                    f"{API_BASE}/v3/images/generate",
                    json={
                        "prompt": prompt,
                        "n": 1,
                        "size": {"width": 1024, "height": 1024},
                        "contentClass": "art",
                    },
                    headers={
                        "Authorization": f"Bearer {token}",
                        "x-api-key": self.client_id,
                        "Content-Type": "application/json",
                    },
                )

                if response.status_code != 200:
                    return BatchResult(
                        prompt=prompt,
                        success=False,
                        error=f"API error: {response.status_code}",
                        duration=time.time() - start_time,
                    )

                result = response.json()
                images = result.get("images", [])

                progress.advance(task_id)

                return BatchResult(
                    prompt=prompt,
                    success=True,
                    url=images[0]["url"] if images else None,
                    duration=time.time() - start_time,
                )

            except Exception as e:
                progress.advance(task_id)
                return BatchResult(
                    prompt=prompt,
                    success=False,
                    error=str(e),
                    duration=time.time() - start_time,
                )

    async def process_batch(self, prompts: list[str]) -> list[BatchResult]:
        """Process multiple prompts in parallel."""
        with Progress() as progress:
            task = progress.add_task("[cyan]Generating images...", total=len(prompts))

            tasks = [
                self.generate_image(prompt, progress, task)
                for prompt in prompts
            ]

            results = await asyncio.gather(*tasks)

        return results


async def main():
    # Example batch of prompts
    prompts = [
        "A serene Japanese garden with cherry blossoms",
        "A cyberpunk city at night with neon lights",
        "A cozy cabin in a snowy forest",
        "An underwater coral reef teeming with colorful fish",
        "A steampunk airship flying through clouds",
        "A mystical forest with glowing mushrooms",
    ]

    console.print("\n[bold blue]Adobe Firefly Batch Processing[/bold blue]")
    console.print(f"[dim]Processing {len(prompts)} prompts...[/dim]\n")

    async with BatchProcessor(max_concurrent=3) as processor:
        results = await processor.process_batch(prompts)

    # Display results
    table = Table(title="Batch Results")
    table.add_column("Prompt", style="cyan", max_width=40)
    table.add_column("Status", style="bold")
    table.add_column("Duration", style="yellow")
    table.add_column("URL/Error", style="dim", max_width=50)

    success_count = 0
    total_duration = 0.0

    for result in results:
        status = "[green]Success[/green]" if result.success else "[red]Failed[/red]"
        duration = f"{result.duration:.1f}s"
        detail = result.url[:50] + "..." if result.url else result.error or ""

        if result.success:
            success_count += 1
        total_duration += result.duration

        table.add_row(
            result.prompt[:40],
            status,
            duration,
            detail,
        )

    console.print(table)
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Successful: {success_count}/{len(results)}")
    console.print(f"  Total time: {total_duration:.1f}s")
    console.print(f"  Avg time per image: {total_duration/len(results):.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
