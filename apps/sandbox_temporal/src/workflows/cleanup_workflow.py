"""Scheduled cleanup workflow for orphaned sandboxes.

Runs periodically to find and clean up sandboxes that:
- Have no associated workflow
- Are older than max age threshold
"""

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from ..activities import (
        find_orphaned_sandboxes,
        cleanup_orphaned_sandboxes,
    )


@workflow.defn
class ScheduledCleanupWorkflow:
    """
    Periodically clean up orphaned sandboxes.

    This workflow runs continuously, checking for orphaned
    sandboxes every interval and cleaning them up.
    """

    def __init__(self):
        self.cleanup_count = 0
        self.last_cleanup_time = None
        self.should_stop = False

    @workflow.run
    async def run(
        self,
        interval_minutes: int = 15,
        max_age_minutes: int = 180,
    ) -> dict:
        """
        Run the cleanup workflow.

        Args:
            interval_minutes: How often to check for orphans
            max_age_minutes: Maximum age for sandboxes to check

        Returns:
            Summary of cleanup operations
        """
        workflow.logger.info(
            f"Starting cleanup workflow: interval={interval_minutes}m, "
            f"max_age={max_age_minutes}m"
        )

        while not self.should_stop:
            try:
                # Find orphaned sandboxes
                orphans = await workflow.execute_activity(
                    find_orphaned_sandboxes,
                    args=[max_age_minutes],
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=RetryPolicy(
                        maximum_attempts=3,
                        initial_interval=timedelta(seconds=5),
                    ),
                )

                if orphans:
                    # Clean them up
                    cleaned = await workflow.execute_activity(
                        cleanup_orphaned_sandboxes,
                        args=[orphans],
                        start_to_close_timeout=timedelta(minutes=10),
                        retry_policy=RetryPolicy(
                            maximum_attempts=2,
                            initial_interval=timedelta(seconds=5),
                        ),
                    )

                    self.cleanup_count += cleaned
                    self.last_cleanup_time = workflow.now()

                    workflow.logger.info(
                        f"Cleaned up {cleaned} orphaned sandboxes "
                        f"(total: {self.cleanup_count})"
                    )
                else:
                    workflow.logger.debug("No orphaned sandboxes found")

            except Exception as e:
                workflow.logger.error(f"Cleanup iteration failed: {e}")

            # Wait for next interval
            await workflow.sleep(timedelta(minutes=interval_minutes))

        return {
            "total_cleaned": self.cleanup_count,
            "last_cleanup": str(self.last_cleanup_time) if self.last_cleanup_time else None,
        }

    @workflow.signal
    def stop(self):
        """Stop the cleanup workflow."""
        self.should_stop = True
        workflow.logger.info("Cleanup workflow stop requested")

    @workflow.query
    def get_stats(self) -> dict:
        """Get cleanup statistics."""
        return {
            "total_cleaned": self.cleanup_count,
            "last_cleanup": str(self.last_cleanup_time) if self.last_cleanup_time else None,
            "running": not self.should_stop,
        }
