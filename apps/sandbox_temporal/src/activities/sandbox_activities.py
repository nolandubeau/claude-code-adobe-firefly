"""Temporal activities for E2B sandbox operations.

These activities wrap E2B SDK calls with:
- Heartbeating for long-running operations
- Structured logging
- Error categorization for retry decisions
"""

import asyncio
import os
from datetime import datetime
from typing import Optional

import structlog
from temporalio import activity
from e2b import Sandbox

from ..models import (
    SandboxInfo,
    CommandInput,
    CommandResult,
    CleanupInput,
    HealthCheckResult,
)

log = structlog.get_logger()


class SandboxCreationError(Exception):
    """Error during sandbox creation."""
    pass


class SandboxConnectionError(Exception):
    """Error connecting to sandbox."""
    pass


class SandboxCommandError(Exception):
    """Error executing command in sandbox."""
    pass


@activity.defn
async def create_sandbox(
    template: str = "base",
    timeout_seconds: int = 300,
    envs: Optional[dict[str, str]] = None,
    metadata: Optional[dict[str, str]] = None,
) -> SandboxInfo:
    """
    Create a new E2B sandbox with health verification.

    Args:
        template: Sandbox template name
        timeout_seconds: Sandbox timeout
        envs: Environment variables
        metadata: Custom metadata

    Returns:
        SandboxInfo with sandbox details

    Raises:
        SandboxCreationError: If sandbox creation fails
    """
    activity.heartbeat("creating_sandbox")

    workflow_id = activity.info().workflow_id
    activity_id = activity.info().activity_id

    logger = log.bind(
        activity="create_sandbox",
        workflow_id=workflow_id,
        activity_id=activity_id,
        template=template,
    )

    logger.info("creating_sandbox")

    try:
        # Merge environment variables with required ones
        sandbox_envs = envs or {}

        # Pass through API keys if available
        if anthropic_key := os.getenv("ANTHROPIC_API_KEY"):
            sandbox_envs["ANTHROPIC_API_KEY"] = anthropic_key
        if github_token := os.getenv("GITHUB_TOKEN"):
            sandbox_envs["GITHUB_TOKEN"] = github_token

        # Add workflow metadata
        sandbox_metadata = metadata or {}
        sandbox_metadata["temporal_workflow_id"] = workflow_id
        sandbox_metadata["temporal_activity_id"] = activity_id

        # Create sandbox in thread pool (E2B SDK is sync)
        sbx = await asyncio.to_thread(
            Sandbox.create,
            template=template,
            timeout=timeout_seconds,
            envs=sandbox_envs,
            metadata=sandbox_metadata,
        )

        activity.heartbeat("sandbox_created")

        # Verify sandbox is healthy
        hostname = await asyncio.to_thread(sbx.get_host, 80)

        activity.heartbeat("sandbox_verified")

        info = SandboxInfo(
            sandbox_id=sbx.sandbox_id,
            template_id=template,
            started_at=datetime.now(),
            hostname=hostname,
            is_running=True,
        )

        logger.info(
            "sandbox_created",
            sandbox_id=info.sandbox_id,
            hostname=hostname,
        )

        return info

    except Exception as e:
        logger.error("sandbox_creation_failed", error=str(e), exc_info=True)
        raise SandboxCreationError(f"Failed to create sandbox: {e}") from e


@activity.defn
async def execute_command(input: CommandInput) -> CommandResult:
    """
    Execute a command in a sandbox with heartbeat.

    Args:
        input: Command execution input

    Returns:
        CommandResult with stdout, stderr, exit_code

    Raises:
        SandboxCommandError: If command execution fails
    """
    activity.heartbeat(f"executing: {input.command[:50]}...")

    logger = log.bind(
        activity="execute_command",
        workflow_id=activity.info().workflow_id,
        sandbox_id=input.sandbox_id,
        command=input.command[:100],
    )

    logger.info("executing_command")

    try:
        # Connect to sandbox
        sbx = await asyncio.to_thread(Sandbox.connect, input.sandbox_id)

        activity.heartbeat("connected")

        # Execute command
        result = await asyncio.to_thread(
            sbx.commands.run,
            input.command,
            cwd=input.cwd,
            timeout=input.timeout_seconds,
            envs=input.envs,
        )

        activity.heartbeat("command_completed")

        cmd_result = CommandResult(
            stdout=result.stdout or "",
            stderr=result.stderr or "",
            exit_code=result.exit_code,
        )

        logger.info(
            "command_completed",
            exit_code=cmd_result.exit_code,
            stdout_len=len(cmd_result.stdout),
            stderr_len=len(cmd_result.stderr),
        )

        return cmd_result

    except Exception as e:
        logger.error("command_execution_failed", error=str(e), exc_info=True)
        raise SandboxCommandError(f"Command execution failed: {e}") from e


@activity.defn
async def cleanup_sandbox(input: CleanupInput) -> bool:
    """
    Kill a sandbox (idempotent).

    Args:
        input: Cleanup input with sandbox_id

    Returns:
        True if cleanup succeeded
    """
    logger = log.bind(
        activity="cleanup_sandbox",
        workflow_id=activity.info().workflow_id,
        sandbox_id=input.sandbox_id,
    )

    logger.info("cleaning_up_sandbox")

    try:
        # Attempt to kill sandbox
        await asyncio.to_thread(Sandbox.kill, input.sandbox_id)
        logger.info("sandbox_killed")
        return True

    except Exception as e:
        # Sandbox might already be dead - that's fine
        logger.warning("sandbox_cleanup_warning", error=str(e))
        return True


@activity.defn
async def health_check(sandbox_id: str) -> HealthCheckResult:
    """
    Check if a sandbox is healthy and running.

    Args:
        sandbox_id: Sandbox ID to check

    Returns:
        HealthCheckResult with health status
    """
    logger = log.bind(
        activity="health_check",
        workflow_id=activity.info().workflow_id,
        sandbox_id=sandbox_id,
    )

    try:
        # Try to connect and check status
        sbx = await asyncio.to_thread(Sandbox.connect, sandbox_id)
        is_running = await asyncio.to_thread(sbx.is_running)

        # Try a simple command to verify responsiveness
        if is_running:
            try:
                result = await asyncio.to_thread(
                    sbx.commands.run,
                    "echo health_check",
                    timeout=10,
                )
                is_healthy = result.exit_code == 0
            except Exception:
                is_healthy = False
        else:
            is_healthy = False

        logger.info(
            "health_check_completed",
            is_healthy=is_healthy,
            is_running=is_running,
        )

        return HealthCheckResult(
            sandbox_id=sandbox_id,
            is_healthy=is_healthy,
            is_running=is_running,
        )

    except Exception as e:
        logger.warning("health_check_failed", error=str(e))
        return HealthCheckResult(
            sandbox_id=sandbox_id,
            is_healthy=False,
            is_running=False,
            error=str(e),
        )


@activity.defn
async def get_sandbox_info(sandbox_id: str) -> SandboxInfo:
    """
    Get detailed information about a sandbox.

    Args:
        sandbox_id: Sandbox ID

    Returns:
        SandboxInfo with sandbox details
    """
    logger = log.bind(
        activity="get_sandbox_info",
        sandbox_id=sandbox_id,
    )

    try:
        info = await asyncio.to_thread(Sandbox.get_info, sandbox_id)

        return SandboxInfo(
            sandbox_id=info.sandbox_id,
            template_id=info.template_id,
            started_at=info.started_at,
            is_running=True,
        )

    except Exception as e:
        logger.error("get_info_failed", error=str(e))
        raise
