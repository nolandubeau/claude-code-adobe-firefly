"""Pydantic schemas for sandbox orchestration."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class ForkStatus(str, Enum):
    """Status of a fork execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    BUDGET_EXCEEDED = "budget_exceeded"


@dataclass
class OrchestrationConfig:
    """Configuration for sandbox orchestration workflow."""
    repo_url: str
    branch: str
    prompt: str
    num_forks: int = 1
    model: str = "sonnet"
    max_concurrent: int = 5
    fork_timeout_seconds: int = 7200  # 2 hours
    budget_limit_usd: Optional[float] = None
    template: str = "base"
    sandbox_timeout_seconds: int = 300


@dataclass
class ForkConfig:
    """Configuration for a single fork workflow."""
    fork_num: int
    repo_url: str
    branch: str
    prompt: str
    model: str = "sonnet"
    timeout_seconds: int = 7200
    budget_limit_usd: Optional[float] = None
    template: str = "base"
    sandbox_timeout_seconds: int = 300


@dataclass
class ForkResult:
    """Result of a single fork execution."""
    fork_num: int
    status: ForkStatus
    sandbox_id: Optional[str] = None
    cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    duration_seconds: float = 0.0
    error: Optional[str] = None
    output: Optional[str] = None


@dataclass
class OrchestrationResult:
    """Result of the orchestration workflow."""
    workflow_id: str
    total_forks: int
    successful: int
    failed: int
    total_cost_usd: float
    total_duration_seconds: float
    results: list[ForkResult]


@dataclass
class SandboxInfo:
    """Information about a sandbox."""
    sandbox_id: str
    template_id: str
    started_at: datetime
    hostname: Optional[str] = None
    is_running: bool = True


@dataclass
class CommandInput:
    """Input for executing a command in a sandbox."""
    sandbox_id: str
    command: str
    cwd: Optional[str] = None
    timeout_seconds: int = 300
    envs: Optional[dict[str, str]] = None


@dataclass
class CommandResult:
    """Result of a command execution."""
    stdout: str
    stderr: str
    exit_code: int


@dataclass
class AgentInput:
    """Input for running a Claude agent."""
    sandbox_id: str
    prompt: str
    model: str
    fork_num: int
    repo_url: str
    branch: str
    max_turns: int = 100


@dataclass
class AgentResult:
    """Result of agent execution."""
    status: ForkStatus
    cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    output: Optional[str] = None
    error: Optional[str] = None


@dataclass
class CleanupInput:
    """Input for sandbox cleanup."""
    sandbox_id: str


@dataclass
class HealthCheckResult:
    """Result of a sandbox health check."""
    sandbox_id: str
    is_healthy: bool
    is_running: bool
    error: Optional[str] = None
