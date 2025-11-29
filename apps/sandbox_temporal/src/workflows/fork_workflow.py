"""Fork workflow for single sandbox execution.

This workflow handles a single fork:
1. Creates sandbox
2. Runs Claude agent
3. Cleans up sandbox (always)

With full durability - can resume from any point after crash.
"""

import time
from datetime import timedelta
from typing import Optional

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError, ApplicationError

with workflow.unsafe.imports_passed_through():
    from ..models import (
        ForkConfig,
        ForkResult,
        ForkStatus,
        CleanupInput,
        AgentInput,
    )
    from ..activities import (
        create_sandbox,
        run_claude_agent,
        cleanup_sandbox,
        health_check,
        get_current_spend,
    )


@workflow.defn
class ForkWorkflow:
    """
    Workflow for a single fork execution with full durability.

    Features:
    - Automatic retry on transient failures
    - Health checks before agent execution
    - Budget enforcement
    - Guaranteed cleanup
    """

    def __init__(self):
        self.config: Optional[ForkConfig] = None
        self.sandbox_id: Optional[str] = None
        self.status = ForkStatus.PENDING
        self.cost_usd = 0.0
        self.should_cancel = False

    @workflow.run
    async def run(self, config: ForkConfig) -> ForkResult:
        """
        Execute a single fork workflow.

        Args:
            config: Fork configuration

        Returns:
            ForkResult with execution details
        """
        self.config = config
        self.status = ForkStatus.RUNNING
        start_time = time.time()

        workflow.logger.info(
            f"Starting fork {config.fork_num}: "
            f"repo={config.repo_url}, branch={config.branch}"
        )

        try:
            # Check budget before starting
            if config.budget_limit_usd:
                current_spend = await workflow.execute_activity(
                    get_current_spend,
                    args=[workflow.info().parent_workflow_id or workflow.info().workflow_id],
                    start_to_close_timeout=timedelta(seconds=30),
                )

                if current_spend >= config.budget_limit_usd:
                    self.status = ForkStatus.BUDGET_EXCEEDED
                    return ForkResult(
                        fork_num=config.fork_num,
                        status=ForkStatus.BUDGET_EXCEEDED,
                        error=f"Budget limit ${config.budget_limit_usd} exceeded (current: ${current_spend})",
                        duration_seconds=time.time() - start_time,
                    )

            # 1. Create sandbox with retry
            sandbox_info = await workflow.execute_activity(
                create_sandbox,
                args=[
                    config.template,
                    config.sandbox_timeout_seconds,
                    None,  # envs
                    {"fork_num": str(config.fork_num)},  # metadata
                ],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=5),
                    backoff_coefficient=2.0,
                    non_retryable_error_types=["SandboxCreationError"],
                ),
            )

            self.sandbox_id = sandbox_info.sandbox_id
            workflow.logger.info(f"Created sandbox: {self.sandbox_id}")

            # 2. Health check
            health = await workflow.execute_activity(
                health_check,
                args=[self.sandbox_id],
                start_to_close_timeout=timedelta(minutes=1),
            )

            if not health.is_healthy:
                raise ApplicationError(
                    f"Sandbox {self.sandbox_id} is not healthy: {health.error}",
                    non_retryable=True,
                )

            # 3. Run Claude agent with heartbeat
            agent_input = AgentInput(
                sandbox_id=self.sandbox_id,
                prompt=config.prompt,
                model=config.model,
                fork_num=config.fork_num,
                repo_url=config.repo_url,
                branch=config.branch,
            )

            agent_result = await workflow.execute_activity(
                run_claude_agent,
                args=[agent_input],
                start_to_close_timeout=timedelta(seconds=config.timeout_seconds),
                heartbeat_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(
                    maximum_attempts=2,
                    initial_interval=timedelta(seconds=10),
                    backoff_coefficient=2.0,
                    non_retryable_error_types=[
                        "AgentBudgetExceededError",
                        "AgentTimeoutError",
                    ],
                ),
            )

            self.cost_usd = agent_result.cost_usd
            self.status = agent_result.status

            duration = time.time() - start_time

            workflow.logger.info(
                f"Fork {config.fork_num} completed: "
                f"status={self.status.value}, cost=${self.cost_usd:.4f}, "
                f"duration={duration:.1f}s"
            )

            return ForkResult(
                fork_num=config.fork_num,
                status=self.status,
                sandbox_id=self.sandbox_id,
                cost_usd=self.cost_usd,
                input_tokens=agent_result.input_tokens,
                output_tokens=agent_result.output_tokens,
                duration_seconds=duration,
                output=agent_result.output,
                error=agent_result.error,
            )

        except Exception as e:
            self.status = ForkStatus.FAILED
            duration = time.time() - start_time

            workflow.logger.error(f"Fork {config.fork_num} failed: {e}")

            return ForkResult(
                fork_num=config.fork_num,
                status=ForkStatus.FAILED,
                sandbox_id=self.sandbox_id,
                cost_usd=self.cost_usd,
                duration_seconds=duration,
                error=str(e),
            )

        finally:
            # 4. Always cleanup sandbox
            if self.sandbox_id:
                try:
                    await workflow.execute_activity(
                        cleanup_sandbox,
                        args=[CleanupInput(sandbox_id=self.sandbox_id)],
                        start_to_close_timeout=timedelta(minutes=2),
                        retry_policy=RetryPolicy(
                            maximum_attempts=3,
                            initial_interval=timedelta(seconds=2),
                        ),
                    )
                    workflow.logger.info(f"Cleaned up sandbox: {self.sandbox_id}")
                except Exception as e:
                    workflow.logger.warning(f"Cleanup failed: {e}")

    @workflow.signal
    def cancel_execution(self):
        """Signal to cancel execution."""
        self.should_cancel = True
        workflow.logger.info(f"Cancel requested for fork {self.config.fork_num if self.config else 'unknown'}")

    @workflow.query
    def get_status(self) -> dict:
        """Get current fork status."""
        return {
            "fork_num": self.config.fork_num if self.config else None,
            "status": self.status.value,
            "sandbox_id": self.sandbox_id,
            "cost_usd": self.cost_usd,
        }
