"""Temporal activities for Claude agent execution.

Runs Claude Code SDK agent inside sandbox with:
- Periodic heartbeating
- Cost and token tracking
- Structured logging
"""

import asyncio
import os
from typing import Optional

import structlog
from temporalio import activity
from e2b import Sandbox

from ..models import AgentInput, AgentResult, ForkStatus

log = structlog.get_logger()


class AgentExecutionError(Exception):
    """Error during agent execution."""
    pass


class AgentTimeoutError(Exception):
    """Agent execution timed out."""
    pass


class AgentBudgetExceededError(Exception):
    """Agent exceeded budget limit."""
    pass


# System prompt template for sandbox agent
SYSTEM_PROMPT_TEMPLATE = """You are an AI assistant executing tasks in an isolated E2B sandbox environment.

## Context
- Repository: {repo_url}
- Branch: {branch}
- Fork Number: {fork_num}

## Instructions
1. Clone the repository and checkout the specified branch
2. Complete the user's task
3. Commit your changes with descriptive messages
4. Push to the remote branch

## Available Tools
You have access to sandbox tools for:
- File operations (read, write, list)
- Command execution (git, npm, python, etc.)
- Process management

## Guidelines
- Always verify your changes work before committing
- Use meaningful commit messages
- Handle errors gracefully
- Report progress regularly
"""


@activity.defn
async def run_claude_agent(input: AgentInput) -> AgentResult:
    """
    Run Claude Code agent in sandbox with heartbeating.

    This activity executes the Claude Code CLI inside the E2B sandbox,
    streaming output and tracking costs.

    Args:
        input: Agent execution input

    Returns:
        AgentResult with execution details

    Raises:
        AgentExecutionError: If agent execution fails
        AgentTimeoutError: If agent times out
    """
    workflow_id = activity.info().workflow_id

    logger = log.bind(
        activity="run_claude_agent",
        workflow_id=workflow_id,
        sandbox_id=input.sandbox_id,
        fork_num=input.fork_num,
        model=input.model,
    )

    logger.info("starting_agent_execution")
    activity.heartbeat({"status": "starting", "fork_num": input.fork_num})

    try:
        # Connect to sandbox
        sbx = await asyncio.to_thread(Sandbox.connect, input.sandbox_id)

        # Format system prompt
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            repo_url=input.repo_url,
            branch=input.branch,
            fork_num=input.fork_num,
        )

        activity.heartbeat({"status": "connected", "fork_num": input.fork_num})

        # Clone repository first
        clone_cmd = f"git clone {input.repo_url} /workspace && cd /workspace && git checkout -b {input.branch} origin/{input.branch} 2>/dev/null || git checkout {input.branch}"

        logger.info("cloning_repository", repo_url=input.repo_url, branch=input.branch)

        clone_result = await asyncio.to_thread(
            sbx.commands.run,
            clone_cmd,
            timeout=300,  # 5 minutes for clone
        )

        if clone_result.exit_code != 0:
            logger.warning(
                "clone_warning",
                stderr=clone_result.stderr,
                exit_code=clone_result.exit_code,
            )

        activity.heartbeat({"status": "repo_cloned", "fork_num": input.fork_num})

        # Prepare Claude Code command
        # Escape the prompt for shell
        escaped_prompt = input.prompt.replace("'", "'\"'\"'")
        escaped_system = system_prompt.replace("'", "'\"'\"'")

        claude_cmd = f"""cd /workspace && echo '{escaped_prompt}' | claude -p \\
            --model {input.model} \\
            --max-turns {input.max_turns} \\
            --dangerously-skip-permissions \\
            --output-format json 2>&1"""

        logger.info("executing_claude_agent", model=input.model, max_turns=input.max_turns)

        # Start heartbeat task
        heartbeat_task = asyncio.create_task(_heartbeat_loop(input.fork_num))

        try:
            # Execute Claude Code CLI
            # Use longer timeout for agent execution
            result = await asyncio.to_thread(
                sbx.commands.run,
                claude_cmd,
                cwd="/workspace",
                timeout=input.max_turns * 60,  # ~1 minute per turn max
            )

            activity.heartbeat({"status": "completed", "fork_num": input.fork_num})

            # Parse result
            output = result.stdout or ""
            stderr = result.stderr or ""

            # Try to extract cost info from JSON output
            cost_usd = 0.0
            input_tokens = 0
            output_tokens = 0

            # Look for cost info in output
            import json
            import re

            # Try to find JSON in output
            json_match = re.search(r'\{[^{}]*"cost"[^{}]*\}', output)
            if json_match:
                try:
                    cost_data = json.loads(json_match.group())
                    cost_usd = cost_data.get("cost", 0.0)
                    input_tokens = cost_data.get("input_tokens", 0)
                    output_tokens = cost_data.get("output_tokens", 0)
                except json.JSONDecodeError:
                    pass

            status = ForkStatus.SUCCESS if result.exit_code == 0 else ForkStatus.FAILED
            error = stderr if result.exit_code != 0 else None

            logger.info(
                "agent_execution_completed",
                status=status.value,
                exit_code=result.exit_code,
                cost_usd=cost_usd,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )

            return AgentResult(
                status=status,
                cost_usd=cost_usd,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                output=output[:10000],  # Truncate output
                error=error,
            )

        finally:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

    except asyncio.TimeoutError as e:
        logger.error("agent_timeout", error=str(e))
        raise AgentTimeoutError(f"Agent execution timed out: {e}") from e

    except Exception as e:
        logger.error("agent_execution_failed", error=str(e), exc_info=True)
        raise AgentExecutionError(f"Agent execution failed: {e}") from e


async def _heartbeat_loop(fork_num: int):
    """Background task to send periodic heartbeats."""
    iteration = 0
    while True:
        await asyncio.sleep(30)  # Heartbeat every 30 seconds
        iteration += 1
        activity.heartbeat({
            "status": "running",
            "fork_num": fork_num,
            "heartbeat_iteration": iteration,
        })
