"""Main orchestration workflow for parallel sandbox forks.

This workflow:
1. Launches multiple fork workflows in parallel (with rate limiting)
2. Collects results from all forks
3. Provides query/signal interfaces for monitoring
4. Handles cancellation gracefully
"""

from datetime import timedelta
from typing import Optional

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError

with workflow.unsafe.imports_passed_through():
    from ..models import (
        OrchestrationConfig,
        OrchestrationResult,
        ForkConfig,
        ForkResult,
        ForkStatus,
    )
    from ..activities import record_metrics


@workflow.defn
class SandboxOrchestrationWorkflow:
    """
    Main workflow that orchestrates parallel fork workflows.

    Features:
    - Rate-limited parallel execution
    - Progress tracking via queries
    - Cancellation via signals
    - Cost aggregation
    """

    def __init__(self):
        self.config: Optional[OrchestrationConfig] = None
        self.results: list[ForkResult] = []
        self.forks_completed = 0
        self.forks_failed = 0
        self.forks_in_progress = 0
        self.total_cost = 0.0
        self.paused = False
        self.cancelled = False

    @workflow.run
    async def run(self, config: OrchestrationConfig) -> OrchestrationResult:
        """
        Execute the orchestration workflow.

        Args:
            config: Orchestration configuration

        Returns:
            OrchestrationResult with all fork results
        """
        self.config = config
        workflow_id = workflow.info().workflow_id

        workflow.logger.info(
            f"Starting orchestration: {config.num_forks} forks, "
            f"max_concurrent={config.max_concurrent}"
        )

        # Launch fork workflows with rate limiting
        fork_handles = []

        for i in range(config.num_forks):
            # Check for cancellation
            if self.cancelled:
                workflow.logger.info("Orchestration cancelled, stopping new forks")
                break

            # Wait while paused
            while self.paused and not self.cancelled:
                await workflow.wait_condition(
                    lambda: not self.paused or self.cancelled,
                    timeout=timedelta(seconds=10),
                )

            # Rate limiting: wait if at max concurrent
            while self.forks_in_progress >= config.max_concurrent:
                await workflow.wait_condition(
                    lambda: self.forks_in_progress < config.max_concurrent,
                    timeout=timedelta(seconds=5),
                )

            # Create fork config
            fork_num = i + 1
            fork_branch = (
                f"{config.branch}-{fork_num}"
                if config.num_forks > 1
                else config.branch
            )

            fork_config = ForkConfig(
                fork_num=fork_num,
                repo_url=config.repo_url,
                branch=fork_branch,
                prompt=config.prompt,
                model=config.model,
                timeout_seconds=config.fork_timeout_seconds,
                budget_limit_usd=config.budget_limit_usd,
                template=config.template,
                sandbox_timeout_seconds=config.sandbox_timeout_seconds,
            )

            # Start child workflow
            handle = await workflow.start_child_workflow(
                "ForkWorkflow",
                fork_config,
                id=f"{workflow_id}-fork-{fork_num}",
                retry_policy=RetryPolicy(
                    maximum_attempts=2,
                    initial_interval=timedelta(seconds=10),
                    backoff_coefficient=2.0,
                ),
                execution_timeout=timedelta(seconds=config.fork_timeout_seconds + 300),
            )

            fork_handles.append((fork_num, handle))
            self.forks_in_progress += 1

            workflow.logger.info(f"Started fork {fork_num}")

        # Collect results
        for fork_num, handle in fork_handles:
            try:
                result = await handle.result()
                self.results.append(result)

                if result.status == ForkStatus.SUCCESS:
                    self.forks_completed += 1
                else:
                    self.forks_failed += 1

                self.total_cost += result.cost_usd

                workflow.logger.info(
                    f"Fork {fork_num} completed: {result.status.value}, "
                    f"cost=${result.cost_usd:.4f}"
                )

                # Record metrics
                await workflow.execute_activity(
                    record_metrics,
                    args=[workflow_id, result],
                    start_to_close_timeout=timedelta(seconds=30),
                )

            except Exception as e:
                self.forks_failed += 1
                self.results.append(
                    ForkResult(
                        fork_num=fork_num,
                        status=ForkStatus.FAILED,
                        error=str(e),
                    )
                )
                workflow.logger.error(f"Fork {fork_num} failed: {e}")

            finally:
                self.forks_in_progress -= 1

        # Calculate total duration
        info = workflow.info()
        duration = (
            workflow.now() - info.start_time
        ).total_seconds() if info.start_time else 0

        return OrchestrationResult(
            workflow_id=workflow_id,
            total_forks=config.num_forks,
            successful=self.forks_completed,
            failed=self.forks_failed,
            total_cost_usd=self.total_cost,
            total_duration_seconds=duration,
            results=self.results,
        )

    @workflow.signal
    def pause(self):
        """Pause starting new forks."""
        self.paused = True
        workflow.logger.info("Orchestration paused")

    @workflow.signal
    def resume(self):
        """Resume starting new forks."""
        self.paused = False
        workflow.logger.info("Orchestration resumed")

    @workflow.signal
    def cancel(self):
        """Cancel the orchestration (finish in-progress forks)."""
        self.cancelled = True
        workflow.logger.info("Orchestration cancellation requested")

    @workflow.query
    def get_progress(self) -> dict:
        """Get current progress."""
        return {
            "total_forks": self.config.num_forks if self.config else 0,
            "completed": self.forks_completed,
            "failed": self.forks_failed,
            "in_progress": self.forks_in_progress,
            "total_cost_usd": self.total_cost,
            "paused": self.paused,
            "cancelled": self.cancelled,
        }

    @workflow.query
    def get_results(self) -> list[dict]:
        """Get current results."""
        return [
            {
                "fork_num": r.fork_num,
                "status": r.status.value,
                "cost_usd": r.cost_usd,
                "duration_seconds": r.duration_seconds,
                "error": r.error,
            }
            for r in self.results
        ]
