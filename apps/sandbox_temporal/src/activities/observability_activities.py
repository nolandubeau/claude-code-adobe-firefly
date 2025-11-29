"""Temporal activities for observability and metrics.

Handles:
- Prometheus metrics recording
- Cost tracking and budget monitoring
- Orphaned sandbox detection
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

import structlog
from temporalio import activity
from e2b import Sandbox

from ..models import ForkResult, ForkStatus

log = structlog.get_logger()

# In-memory cost tracking (would be Redis/DB in production)
_cost_tracker: dict[str, float] = {}


@activity.defn
async def record_metrics(
    workflow_id: str,
    fork_result: ForkResult,
) -> None:
    """
    Record metrics for a completed fork.

    Args:
        workflow_id: Parent workflow ID
        fork_result: Result of fork execution
    """
    logger = log.bind(
        activity="record_metrics",
        workflow_id=workflow_id,
        fork_num=fork_result.fork_num,
    )

    try:
        # Import prometheus client (optional dependency)
        from prometheus_client import Counter, Histogram, Gauge

        # Define metrics (would be module-level in production)
        fork_completed = Counter(
            "sandbox_fork_completed_total",
            "Total forks completed",
            ["status", "model"],
        )

        fork_duration = Histogram(
            "sandbox_fork_duration_seconds",
            "Fork execution duration",
            ["status"],
            buckets=[60, 300, 600, 1800, 3600, 7200],
        )

        fork_cost = Histogram(
            "sandbox_fork_cost_usd",
            "Fork cost in USD",
            ["model"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0],
        )

        # Record metrics
        fork_completed.labels(
            status=fork_result.status.value,
            model="sonnet",  # Would get from config
        ).inc()

        fork_duration.labels(
            status=fork_result.status.value,
        ).observe(fork_result.duration_seconds)

        fork_cost.labels(model="sonnet").observe(fork_result.cost_usd)

        logger.info(
            "metrics_recorded",
            status=fork_result.status.value,
            cost_usd=fork_result.cost_usd,
            duration=fork_result.duration_seconds,
        )

    except ImportError:
        # Prometheus not available, just log
        logger.info(
            "metrics_logged",
            status=fork_result.status.value,
            cost_usd=fork_result.cost_usd,
            duration=fork_result.duration_seconds,
        )


@activity.defn
async def get_current_spend(workflow_id: str) -> float:
    """
    Get current spend for a workflow.

    Args:
        workflow_id: Workflow ID to check

    Returns:
        Current spend in USD
    """
    return _cost_tracker.get(workflow_id, 0.0)


@activity.defn
async def update_spend(workflow_id: str, cost: float) -> float:
    """
    Update spend for a workflow.

    Args:
        workflow_id: Workflow ID
        cost: Cost to add

    Returns:
        New total spend
    """
    current = _cost_tracker.get(workflow_id, 0.0)
    new_total = current + cost
    _cost_tracker[workflow_id] = new_total
    return new_total


@activity.defn
async def find_orphaned_sandboxes(
    max_age_minutes: int = 180,
) -> list[str]:
    """
    Find sandboxes that may be orphaned (no active workflow).

    Args:
        max_age_minutes: Maximum age for sandboxes to check

    Returns:
        List of potentially orphaned sandbox IDs
    """
    logger = log.bind(activity="find_orphaned_sandboxes")

    try:
        # List all sandboxes
        paginator = Sandbox.list()
        sandboxes = await asyncio.to_thread(paginator.next_items)

        orphaned = []
        cutoff = datetime.now() - timedelta(minutes=max_age_minutes)

        for sbx in sandboxes:
            # Check if sandbox is old enough
            if sbx.started_at < cutoff:
                # Check metadata for workflow association
                metadata = sbx.metadata or {}
                workflow_id = metadata.get("temporal_workflow_id")

                if not workflow_id:
                    # No workflow association - likely orphaned
                    orphaned.append(sbx.sandbox_id)
                    logger.info(
                        "orphaned_sandbox_found",
                        sandbox_id=sbx.sandbox_id,
                        started_at=str(sbx.started_at),
                    )

        logger.info(
            "orphan_scan_completed",
            total_sandboxes=len(sandboxes),
            orphaned_count=len(orphaned),
        )

        return orphaned

    except Exception as e:
        logger.error("orphan_scan_failed", error=str(e))
        return []


@activity.defn
async def cleanup_orphaned_sandboxes(sandbox_ids: list[str]) -> int:
    """
    Clean up orphaned sandboxes.

    Args:
        sandbox_ids: List of sandbox IDs to clean up

    Returns:
        Number of sandboxes cleaned up
    """
    logger = log.bind(activity="cleanup_orphaned_sandboxes")

    cleaned = 0
    for sandbox_id in sandbox_ids:
        try:
            await asyncio.to_thread(Sandbox.kill, sandbox_id)
            cleaned += 1
            logger.info("orphaned_sandbox_killed", sandbox_id=sandbox_id)
        except Exception as e:
            logger.warning(
                "orphan_cleanup_failed",
                sandbox_id=sandbox_id,
                error=str(e),
            )

    return cleaned
