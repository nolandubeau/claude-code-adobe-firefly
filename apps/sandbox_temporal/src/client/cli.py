"""CLI for Temporal-based sandbox orchestration.

Commands:
- fork: Launch parallel sandbox forks
- status: Check workflow status
- cancel: Cancel a workflow
- list: List running workflows
- cleanup: Start cleanup workflow
"""

import asyncio
import os
import uuid
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from temporalio.client import Client, TLSConfig

from ..models import OrchestrationConfig
from ..workflows import SandboxOrchestrationWorkflow, ScheduledCleanupWorkflow

app = typer.Typer(
    name="sandbox-temporal",
    help="Durable sandbox orchestration with Temporal",
)
console = Console()


async def get_client() -> Client:
    """Get Temporal client from environment."""
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")

    # Check for TLS configuration
    tls_config = None
    if cert_path := os.getenv("TEMPORAL_TLS_CERT"):
        key_path = os.getenv("TEMPORAL_TLS_KEY")
        if key_path:
            with open(cert_path, "rb") as f:
                cert = f.read()
            with open(key_path, "rb") as f:
                key = f.read()
            tls_config = TLSConfig(client_cert=cert, client_private_key=key)

    return await Client.connect(
        temporal_address,
        namespace=temporal_namespace,
        tls=tls_config,
    )


@app.command()
def fork(
    repo_url: str = typer.Argument(..., help="Git repository URL"),
    branch: str = typer.Option("main", "--branch", "-b", help="Git branch"),
    prompt: str = typer.Option(..., "--prompt", "-p", help="Prompt for agents"),
    num_forks: int = typer.Option(1, "--forks", "-f", help="Number of forks"),
    model: str = typer.Option("sonnet", "--model", "-m", help="Claude model"),
    max_concurrent: int = typer.Option(5, "--max-concurrent", help="Max concurrent forks"),
    timeout: int = typer.Option(7200, "--timeout", "-t", help="Timeout per fork (seconds)"),
    budget: Optional[float] = typer.Option(None, "--budget", help="Budget limit (USD)"),
    wait: bool = typer.Option(True, "--wait/--no-wait", help="Wait for completion"),
):
    """Launch parallel sandbox forks with Temporal durability."""
    asyncio.run(_fork(
        repo_url, branch, prompt, num_forks, model,
        max_concurrent, timeout, budget, wait
    ))


async def _fork(
    repo_url: str,
    branch: str,
    prompt: str,
    num_forks: int,
    model: str,
    max_concurrent: int,
    timeout: int,
    budget: Optional[float],
    wait: bool,
):
    """Internal fork implementation."""
    client = await get_client()

    config = OrchestrationConfig(
        repo_url=repo_url,
        branch=branch,
        prompt=prompt,
        num_forks=num_forks,
        model=model,
        max_concurrent=max_concurrent,
        fork_timeout_seconds=timeout,
        budget_limit_usd=budget,
    )

    workflow_id = f"sandbox-orch-{uuid.uuid4().hex[:8]}"

    console.print(f"\n[bold blue]Starting orchestration workflow[/bold blue]")
    console.print(f"  Workflow ID: [green]{workflow_id}[/green]")
    console.print(f"  Repository: {repo_url}")
    console.print(f"  Branch: {branch}")
    console.print(f"  Forks: {num_forks}")
    console.print(f"  Model: {model}")
    console.print(f"  Max Concurrent: {max_concurrent}")
    console.print()

    # Start workflow
    handle = await client.start_workflow(
        SandboxOrchestrationWorkflow.run,
        config,
        id=workflow_id,
        task_queue="sandbox-orchestration",
    )

    console.print(f"[green]Workflow started![/green]")
    console.print(f"View in Temporal UI: http://localhost:8080/namespaces/default/workflows/{workflow_id}")
    console.print()

    if not wait:
        console.print("Use [cyan]sandbox-temporal status {workflow_id}[/cyan] to check progress")
        return

    # Wait for result with progress updates
    console.print("[bold]Waiting for completion...[/bold]\n")

    try:
        result = await handle.result()

        # Display results
        table = Table(title="Fork Results")
        table.add_column("Fork", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Cost", style="yellow")
        table.add_column("Duration", style="blue")
        table.add_column("Error", style="red")

        for r in result.results:
            status_style = "green" if r.status.value == "success" else "red"
            table.add_row(
                str(r.fork_num),
                f"[{status_style}]{r.status.value}[/{status_style}]",
                f"${r.cost_usd:.4f}",
                f"{r.duration_seconds:.1f}s",
                r.error[:50] if r.error else "-",
            )

        console.print(table)

        # Summary panel
        summary = Panel(
            f"[bold]Total Forks:[/bold] {result.total_forks}\n"
            f"[bold green]Successful:[/bold green] {result.successful}\n"
            f"[bold red]Failed:[/bold red] {result.failed}\n"
            f"[bold yellow]Total Cost:[/bold yellow] ${result.total_cost_usd:.4f}\n"
            f"[bold blue]Duration:[/bold blue] {result.total_duration_seconds:.1f}s",
            title="Summary",
        )
        console.print(summary)

    except Exception as e:
        console.print(f"[red]Workflow failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def status(
    workflow_id: str = typer.Argument(..., help="Workflow ID to check"),
):
    """Check status of a running workflow."""
    asyncio.run(_status(workflow_id))


async def _status(workflow_id: str):
    """Internal status implementation."""
    client = await get_client()
    handle = client.get_workflow_handle(workflow_id)

    try:
        progress = await handle.query(SandboxOrchestrationWorkflow.get_progress)

        console.print(f"\n[bold]Workflow Progress: {workflow_id}[/bold]\n")

        table = Table()
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Forks", str(progress["total_forks"]))
        table.add_row("Completed", str(progress["completed"]))
        table.add_row("Failed", str(progress["failed"]))
        table.add_row("In Progress", str(progress["in_progress"]))
        table.add_row("Total Cost", f"${progress['total_cost_usd']:.4f}")
        table.add_row("Paused", str(progress["paused"]))
        table.add_row("Cancelled", str(progress["cancelled"]))

        console.print(table)

    except Exception as e:
        console.print(f"[red]Failed to get status: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def cancel(
    workflow_id: str = typer.Argument(..., help="Workflow ID to cancel"),
):
    """Cancel a running workflow."""
    asyncio.run(_cancel(workflow_id))


async def _cancel(workflow_id: str):
    """Internal cancel implementation."""
    client = await get_client()
    handle = client.get_workflow_handle(workflow_id)

    try:
        await handle.signal(SandboxOrchestrationWorkflow.cancel)
        console.print(f"[yellow]Cancel signal sent to {workflow_id}[/yellow]")
        console.print("In-progress forks will complete, no new forks will start.")
    except Exception as e:
        console.print(f"[red]Failed to cancel: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def pause(
    workflow_id: str = typer.Argument(..., help="Workflow ID to pause"),
):
    """Pause a running workflow."""
    asyncio.run(_pause(workflow_id))


async def _pause(workflow_id: str):
    """Internal pause implementation."""
    client = await get_client()
    handle = client.get_workflow_handle(workflow_id)

    try:
        await handle.signal(SandboxOrchestrationWorkflow.pause)
        console.print(f"[yellow]Workflow {workflow_id} paused[/yellow]")
    except Exception as e:
        console.print(f"[red]Failed to pause: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def resume(
    workflow_id: str = typer.Argument(..., help="Workflow ID to resume"),
):
    """Resume a paused workflow."""
    asyncio.run(_resume(workflow_id))


async def _resume(workflow_id: str):
    """Internal resume implementation."""
    client = await get_client()
    handle = client.get_workflow_handle(workflow_id)

    try:
        await handle.signal(SandboxOrchestrationWorkflow.resume)
        console.print(f"[green]Workflow {workflow_id} resumed[/green]")
    except Exception as e:
        console.print(f"[red]Failed to resume: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="list")
def list_workflows(
    limit: int = typer.Option(10, "--limit", "-l", help="Max workflows to show"),
):
    """List running workflows."""
    asyncio.run(_list_workflows(limit))


async def _list_workflows(limit: int):
    """Internal list implementation."""
    client = await get_client()

    console.print("\n[bold]Running Sandbox Workflows[/bold]\n")

    table = Table()
    table.add_column("Workflow ID", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Start Time", style="blue")

    count = 0
    async for workflow in client.list_workflows(
        query="WorkflowType = 'SandboxOrchestrationWorkflow'"
    ):
        if count >= limit:
            break

        table.add_row(
            workflow.id,
            str(workflow.status),
            str(workflow.start_time) if workflow.start_time else "-",
        )
        count += 1

    if count == 0:
        console.print("[dim]No running workflows found[/dim]")
    else:
        console.print(table)


@app.command()
def cleanup(
    interval: int = typer.Option(15, "--interval", "-i", help="Cleanup interval (minutes)"),
    max_age: int = typer.Option(180, "--max-age", help="Max sandbox age (minutes)"),
):
    """Start the scheduled cleanup workflow."""
    asyncio.run(_cleanup(interval, max_age))


async def _cleanup(interval: int, max_age: int):
    """Internal cleanup implementation."""
    client = await get_client()

    workflow_id = "sandbox-cleanup-scheduled"

    console.print(f"\n[bold blue]Starting cleanup workflow[/bold blue]")
    console.print(f"  Interval: {interval} minutes")
    console.print(f"  Max Age: {max_age} minutes")
    console.print()

    try:
        handle = await client.start_workflow(
            ScheduledCleanupWorkflow.run,
            args=[interval, max_age],
            id=workflow_id,
            task_queue="sandbox-orchestration",
        )

        console.print(f"[green]Cleanup workflow started: {workflow_id}[/green]")
        console.print("This workflow will run continuously until stopped.")
        console.print(f"\nTo stop: sandbox-temporal stop-cleanup")

    except Exception as e:
        if "already running" in str(e).lower():
            console.print(f"[yellow]Cleanup workflow already running[/yellow]")
        else:
            console.print(f"[red]Failed to start cleanup: {e}[/red]")
            raise typer.Exit(1)


@app.command(name="stop-cleanup")
def stop_cleanup():
    """Stop the scheduled cleanup workflow."""
    asyncio.run(_stop_cleanup())


async def _stop_cleanup():
    """Internal stop cleanup implementation."""
    client = await get_client()
    handle = client.get_workflow_handle("sandbox-cleanup-scheduled")

    try:
        await handle.signal(ScheduledCleanupWorkflow.stop)
        console.print("[yellow]Cleanup workflow stop signal sent[/yellow]")
    except Exception as e:
        console.print(f"[red]Failed to stop cleanup: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
