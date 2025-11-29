"""Temporal worker for sandbox orchestration.

Runs the worker that processes sandbox workflows and activities.
"""

import asyncio
import os
import signal
import sys
from typing import Optional

import structlog
from temporalio.client import Client, TLSConfig
from temporalio.worker import Worker
from temporalio.runtime import Runtime, TelemetryConfig, PrometheusConfig

from ..workflows import (
    SandboxOrchestrationWorkflow,
    ForkWorkflow,
    ScheduledCleanupWorkflow,
)
from ..activities import (
    create_sandbox,
    execute_command,
    cleanup_sandbox,
    health_check,
    get_sandbox_info,
    run_claude_agent,
    record_metrics,
    get_current_spend,
    find_orphaned_sandboxes,
)
from ..activities.observability_activities import (
    update_spend,
    cleanup_orphaned_sandboxes,
)

log = structlog.get_logger()


def configure_logging():
    """Configure structured logging."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def create_runtime_with_metrics(
    metrics_port: int = 9090,
) -> Optional[Runtime]:
    """
    Create Temporal runtime with Prometheus metrics.

    Args:
        metrics_port: Port for Prometheus metrics endpoint

    Returns:
        Runtime with metrics configured, or None if disabled
    """
    if os.getenv("DISABLE_METRICS"):
        return None

    try:
        return Runtime(
            telemetry=TelemetryConfig(
                metrics=PrometheusConfig(bind_address=f"0.0.0.0:{metrics_port}"),
            )
        )
    except Exception as e:
        log.warning("Failed to create metrics runtime", error=str(e))
        return None


async def create_worker(
    client: Client,
    task_queue: str = "sandbox-orchestration",
) -> Worker:
    """
    Create a Temporal worker with all workflows and activities.

    Args:
        client: Temporal client
        task_queue: Task queue name

    Returns:
        Configured Worker instance
    """
    return Worker(
        client,
        task_queue=task_queue,
        workflows=[
            SandboxOrchestrationWorkflow,
            ForkWorkflow,
            ScheduledCleanupWorkflow,
        ],
        activities=[
            # Sandbox activities
            create_sandbox,
            execute_command,
            cleanup_sandbox,
            health_check,
            get_sandbox_info,
            # Agent activities
            run_claude_agent,
            # Observability activities
            record_metrics,
            get_current_spend,
            update_spend,
            find_orphaned_sandboxes,
            cleanup_orphaned_sandboxes,
        ],
    )


async def run_worker():
    """Run the Temporal worker."""
    configure_logging()

    # Get configuration from environment
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "sandbox-orchestration")
    metrics_port = int(os.getenv("METRICS_PORT", "9090"))

    log.info(
        "Starting sandbox worker",
        temporal_address=temporal_address,
        namespace=temporal_namespace,
        task_queue=task_queue,
    )

    # Create runtime with metrics
    runtime = create_runtime_with_metrics(metrics_port)
    if runtime:
        log.info(f"Metrics available at http://0.0.0.0:{metrics_port}/metrics")

    # Check for TLS configuration (Temporal Cloud)
    tls_config = None
    if cert_path := os.getenv("TEMPORAL_TLS_CERT"):
        key_path = os.getenv("TEMPORAL_TLS_KEY")
        if key_path:
            with open(cert_path, "rb") as f:
                cert = f.read()
            with open(key_path, "rb") as f:
                key = f.read()
            tls_config = TLSConfig(client_cert=cert, client_private_key=key)
            log.info("Using TLS for Temporal connection")

    # Connect to Temporal
    client = await Client.connect(
        temporal_address,
        namespace=temporal_namespace,
        tls=tls_config,
        runtime=runtime,
    )

    log.info("Connected to Temporal server")

    # Create worker
    worker = await create_worker(client, task_queue)

    # Handle shutdown signals
    shutdown_event = asyncio.Event()

    def signal_handler(sig):
        log.info(f"Received signal {sig}, shutting down...")
        shutdown_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        asyncio.get_event_loop().add_signal_handler(
            sig, lambda s=sig: signal_handler(s)
        )

    # Run worker until shutdown
    log.info("Worker started, waiting for tasks...")

    try:
        async with worker:
            await shutdown_event.wait()
    except Exception as e:
        log.error("Worker error", error=str(e), exc_info=True)
        raise

    log.info("Worker shutdown complete")


def main():
    """Entry point for the worker."""
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        print("\nWorker stopped")
        sys.exit(0)


if __name__ == "__main__":
    main()
