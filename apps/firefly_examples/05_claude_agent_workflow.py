#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "httpx>=0.27.0",
#   "python-dotenv>=1.0.0",
#   "rich>=13.7.0",
#   "pydantic>=2.5.0",
# ]
# ///
"""
05 - Claude Agent Workflow with Adobe Firefly

This example demonstrates a multi-step creative workflow using Adobe Firefly,
designed to integrate with Claude Agent SDK.

Run with: uv run apps/firefly_examples/05_claude_agent_workflow.py
"""

import asyncio
import os
import sys
import json
from dataclasses import dataclass
from typing import Any, Optional
from dotenv import load_dotenv
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

load_dotenv()

console = Console()

AUTH_URL = "https://ims-na1.adobelogin.com/ims/token/v3"
API_BASE = "https://firefly-api.adobe.io"
SCOPES = "openid,AdobeID,firefly_api,ff_apis"


@dataclass
class WorkflowStep:
    """A step in the creative workflow."""
    name: str
    description: str
    status: str = "pending"
    result: Optional[dict] = None
    error: Optional[str] = None


class FireflyWorkflowAgent:
    """
    Adobe Firefly Workflow Agent

    Orchestrates multi-step creative workflows using Firefly API.
    Designed for integration with Claude Agent SDK.
    """

    def __init__(self):
        self.client_id = os.getenv("FIREFLY_CLIENT_ID")
        self.client_secret = os.getenv("FIREFLY_CLIENT_SECRET")
        self._token: Optional[str] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        self.steps: list[WorkflowStep] = []

    async def __aenter__(self):
        self._http_client = httpx.AsyncClient(timeout=60.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._http_client:
            await self._http_client.aclose()

    async def _authenticate(self) -> str:
        """Get access token."""
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

    async def _api_call(self, endpoint: str, body: dict) -> dict:
        """Make an API call."""
        token = await self._authenticate()
        response = await self._http_client.post(
            f"{API_BASE}{endpoint}",
            json=body,
            headers={
                "Authorization": f"Bearer {token}",
                "x-api-key": self.client_id,
                "Content-Type": "application/json",
            },
        )

        if response.status_code != 200:
            raise Exception(f"API error: {response.text}")

        return response.json()

    def add_step(self, name: str, description: str) -> WorkflowStep:
        """Add a step to the workflow."""
        step = WorkflowStep(name=name, description=description)
        self.steps.append(step)
        return step

    async def execute_workflow(self, workflow_type: str, params: dict) -> list[dict]:
        """Execute a pre-defined workflow."""
        results = []

        if workflow_type == "product_photography":
            results = await self._product_photography_workflow(params)
        elif workflow_type == "art_series":
            results = await self._art_series_workflow(params)
        elif workflow_type == "concept_exploration":
            results = await self._concept_exploration_workflow(params)
        else:
            raise ValueError(f"Unknown workflow type: {workflow_type}")

        return results

    async def _product_photography_workflow(self, params: dict) -> list[dict]:
        """
        Product Photography Workflow

        1. Generate product image
        2. Remove background
        3. Generate new background
        4. Composite (conceptual - actual compositing would need additional tools)
        """
        results = []
        product_desc = params.get("product", "a minimalist product")
        background_desc = params.get("background", "clean white studio lighting")

        # Step 1: Generate product image
        step1 = self.add_step("generate_product", "Generate initial product image")
        step1.status = "in_progress"
        console.print(f"[cyan]Step 1:[/cyan] Generating product image...")

        result1 = await self._api_call("/v3/images/generate", {
            "prompt": f"Professional product photography of {product_desc}, studio lighting, clean background, 8K detail",
            "n": 1,
            "size": {"width": 1024, "height": 1024},
            "contentClass": "photo",
        })
        step1.result = result1
        step1.status = "completed"
        results.append({"step": "generate_product", "images": result1.get("images", [])})
        console.print(f"[green]✓[/green] Product image generated")

        if result1.get("images"):
            product_url = result1["images"][0]["url"]

            # Step 2: Remove background
            step2 = self.add_step("remove_background", "Remove product background")
            step2.status = "in_progress"
            console.print(f"[cyan]Step 2:[/cyan] Removing background...")

            result2 = await self._api_call("/v2/images/cutout", {
                "image": {"source": {"url": product_url}},
            })
            step2.result = result2
            step2.status = "completed"
            results.append({"step": "remove_background", "url": result2.get("output", {}).get("url")})
            console.print(f"[green]✓[/green] Background removed")

            # Step 3: Generate background
            step3 = self.add_step("generate_background", "Generate new background")
            step3.status = "in_progress"
            console.print(f"[cyan]Step 3:[/cyan] Generating background...")

            result3 = await self._api_call("/v3/images/generate", {
                "prompt": f"Product photography background, {background_desc}, professional studio",
                "n": 1,
                "size": {"width": 1024, "height": 1024},
                "contentClass": "photo",
            })
            step3.result = result3
            step3.status = "completed"
            results.append({"step": "generate_background", "images": result3.get("images", [])})
            console.print(f"[green]✓[/green] Background generated")

        return results

    async def _art_series_workflow(self, params: dict) -> list[dict]:
        """
        Art Series Workflow

        Generate a series of related artistic images.
        """
        results = []
        theme = params.get("theme", "abstract")
        style = params.get("style", "modern art")
        count = params.get("count", 4)

        step = self.add_step("generate_series", f"Generate {count} images in series")
        step.status = "in_progress"

        for i in range(count):
            console.print(f"[cyan]Generating image {i + 1}/{count}...[/cyan]")

            result = await self._api_call("/v3/images/generate", {
                "prompt": f"{theme}, {style}, variation {i + 1}, cohesive series, professional quality",
                "n": 1,
                "size": {"width": 1024, "height": 1024},
                "contentClass": "art",
            })
            results.append({
                "step": f"series_image_{i + 1}",
                "images": result.get("images", [])
            })
            console.print(f"[green]✓[/green] Image {i + 1} complete")

        step.status = "completed"
        return results

    async def _concept_exploration_workflow(self, params: dict) -> list[dict]:
        """
        Concept Exploration Workflow

        Generate multiple variations exploring a concept.
        """
        results = []
        concept = params.get("concept", "futuristic city")
        variations = params.get("variations", 4)

        approaches = [
            "photorealistic rendering",
            "artistic interpretation",
            "minimalist design",
            "dramatic cinematic style",
        ]

        step = self.add_step("explore_concept", f"Explore {variations} variations")
        step.status = "in_progress"

        for i in range(min(variations, len(approaches))):
            console.print(f"[cyan]Exploring variation {i + 1}: {approaches[i]}...[/cyan]")

            result = await self._api_call("/v3/images/generate", {
                "prompt": f"{concept}, {approaches[i]}, high quality, detailed",
                "n": 1,
                "size": {"width": 1024, "height": 1024},
                "contentClass": "art" if "artistic" in approaches[i] else "photo",
            })
            results.append({
                "step": f"variation_{i + 1}",
                "approach": approaches[i],
                "images": result.get("images", [])
            })
            console.print(f"[green]✓[/green] Variation {i + 1} complete")

        step.status = "completed"
        return results

    def print_summary(self, results: list[dict]):
        """Print workflow summary."""
        console.print("\n" + "=" * 60)
        console.print(Panel.fit("[bold green]Workflow Complete[/bold green]"))

        for result in results:
            step_name = result.get("step", "unknown")
            console.print(f"\n[bold]{step_name}:[/bold]")

            if "images" in result:
                for i, img in enumerate(result["images"]):
                    console.print(f"  Image {i + 1}: {img.get('url', 'N/A')}")
            elif "url" in result:
                console.print(f"  URL: {result['url']}")


async def main():
    console.print(Panel.fit("[bold blue]Adobe Firefly Agent Workflow Demo[/bold blue]"))

    # Select workflow type
    workflow_type = sys.argv[1] if len(sys.argv) > 1 else "concept_exploration"

    params = {
        "product_photography": {
            "product": "sleek wireless headphones",
            "background": "marble surface with soft shadows",
        },
        "art_series": {
            "theme": "the four seasons",
            "style": "watercolor painting",
            "count": 4,
        },
        "concept_exploration": {
            "concept": "sustainable architecture of the future",
            "variations": 4,
        },
    }

    if workflow_type not in params:
        console.print(f"[red]Unknown workflow: {workflow_type}[/red]")
        console.print("Available: product_photography, art_series, concept_exploration")
        sys.exit(1)

    console.print(f"[dim]Running workflow: {workflow_type}[/dim]\n")

    async with FireflyWorkflowAgent() as agent:
        results = await agent.execute_workflow(workflow_type, params[workflow_type])
        agent.print_summary(results)


if __name__ == "__main__":
    asyncio.run(main())
