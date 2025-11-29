# Sandbox Durability & Observability Enhancement Plan

## Executive Summary

This plan outlines enhancements to make the E2B sandbox orchestration system production-grade by implementing durable execution patterns inspired by [Temporal.io](https://temporal.io/) and [Motia.dev](https://www.motia.dev/). OpenAI uses Temporal for their image generation queues at scale, handling millions of requests with built-in retry, state persistence, and observability.

### Why This Matters

Current sandbox architecture limitations:
- **No retry logic** - Single transient failure kills entire fork
- **No checkpoint/resume** - Process crash = all progress lost
- **No health monitoring** - Dead sandboxes not detected until use
- **No rate limiting** - 100 concurrent forks could overwhelm E2B API
- **Basic observability** - Logs exist but no queryable metrics

---

## Technology Comparison

### Temporal.io

| Feature | Description |
|---------|-------------|
| **Durable Execution** | Workflows automatically persist state at every step; failures resume exactly where they left off |
| **Event Sourcing** | Full event history for replay, recovery, and debugging |
| **Built-in Retries** | Configurable retry policies with exponential backoff |
| **Task Queues** | Automatic back-pressure; server queues pending tasks |
| **Observability** | Web UI with execution histories, logs, traces; Prometheus/Grafana integration |
| **Signals & Timers** | External events and scheduled operations |
| **Language SDKs** | Python, TypeScript, Go, Java, .NET |

**Production Usage**: Netflix, OpenAI (image generation, Codex), Snap, Stripe

### Motia.dev

| Feature | Description |
|---------|-------------|
| **Step Primitive** | Single abstraction for APIs, jobs, workflows, agents |
| **Event-Based** | All steps communicate via events; automatic retry |
| **State Store** | Unified key-value state across steps |
| **Fault Tolerance** | Built-in without manual queue infrastructure |
| **Traces UI** | Full execution traces with step timelines, state ops, logs |
| **Multi-Language** | TypeScript, Python (coming) |

**Best For**: Unified backend where you want APIs + workflows + agents in one runtime

### Recommendation: **Temporal.io**

**Rationale**:
1. **Proven at Scale** - OpenAI uses it for image generation queues handling massive load
2. **Mature Ecosystem** - 6+ years of production hardening, extensive documentation
3. **Python SDK** - Native integration with existing sandbox Python code
4. **Self-Hosted or Cloud** - Temporal Cloud available, or run your own
5. **OpenAI Agents Integration** - Existing `temporalio.contrib.openai_agents` plugin

---

## Architecture Design

### Current vs. Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CURRENT ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   User CLI → Python Threads → E2B Sandboxes → Claude SDK Agents         │
│                    ↓                                                    │
│              In-Memory Results (lost on crash)                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                        PROPOSED ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   User CLI                                                              │
│      ↓                                                                  │
│   Temporal Client                                                       │
│      ↓                                                                  │
│   ┌───────────────────────────────────────────────────────────────┐     │
│   │                    Temporal Server                            │     │
│   │  ┌─────────────────────────────────────────────────────────┐  │     │
│   │  │              Sandbox Orchestration Workflow              │  │     │
│   │  │                                                          │  │     │
│   │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │  │     │
│   │  │  │  Fork 1  │  │  Fork 2  │  │  Fork N  │  (parallel)  │  │     │
│   │  │  │ Workflow │  │ Workflow │  │ Workflow │              │  │     │
│   │  │  └────┬─────┘  └────┬─────┘  └────┬─────┘              │  │     │
│   │  └───────┼─────────────┼─────────────┼──────────────────────┘  │     │
│   │          │             │             │                         │     │
│   │          ▼             ▼             ▼                         │     │
│   │   ┌─────────────────────────────────────────────────────────┐  │     │
│   │   │                    Activity Workers                     │  │     │
│   │   │  • create_sandbox()     - E2B SDK calls                 │  │     │
│   │   │  • execute_command()    - Sandbox command execution     │  │     │
│   │   │  • run_claude_agent()   - Claude SDK agent loop         │  │     │
│   │   │  • health_check()       - Sandbox status verification   │  │     │
│   │   │  • cleanup_sandbox()    - Kill sandbox on completion    │  │     │
│   │   └─────────────────────────────────────────────────────────┘  │     │
│   │                              │                                  │     │
│   │                              ▼                                  │     │
│   │   ┌─────────────────────────────────────────────────────────┐  │     │
│   │   │              Event History (Durable State)              │  │     │
│   │   │  • Full workflow state persisted                        │  │     │
│   │   │  • Automatic checkpoint on every activity               │  │     │
│   │   │  • Resume from any point after crash                    │  │     │
│   │   └─────────────────────────────────────────────────────────┘  │     │
│   └───────────────────────────────────────────────────────────────┘     │
│                              │                                          │
│                              ▼                                          │
│   ┌───────────────────────────────────────────────────────────────┐     │
│   │                     E2B Sandboxes                             │     │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐                       │     │
│   │  │  Sbx 1  │  │  Sbx 2  │  │  Sbx N  │                       │     │
│   │  │ (Fork 1)│  │ (Fork 2)│  │ (Fork N)│                       │     │
│   │  └─────────┘  └─────────┘  └─────────┘                       │     │
│   └───────────────────────────────────────────────────────────────┘     │
│                              │                                          │
│                              ▼                                          │
│   ┌───────────────────────────────────────────────────────────────┐     │
│   │                    Observability Stack                        │     │
│   │  • Temporal Web UI (workflow visualization)                   │     │
│   │  • Prometheus + Grafana (metrics)                             │     │
│   │  • Custom Dashboard (cost tracking, fork status)              │     │
│   └───────────────────────────────────────────────────────────────┘     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Core Temporal Integration

**Goal**: Replace in-memory orchestration with Temporal workflows

#### 1.1 Project Setup

```bash
# New app directory
apps/sandbox_temporal/
├── src/
│   ├── workflows/
│   │   ├── __init__.py
│   │   ├── sandbox_orchestration.py    # Main orchestration workflow
│   │   ├── fork_workflow.py            # Individual fork workflow
│   │   └── cleanup_workflow.py         # Sandbox cleanup workflow
│   ├── activities/
│   │   ├── __init__.py
│   │   ├── sandbox_activities.py       # E2B operations
│   │   ├── agent_activities.py         # Claude SDK operations
│   │   └── observability_activities.py # Metrics/logging
│   ├── workers/
│   │   ├── __init__.py
│   │   └── sandbox_worker.py           # Activity worker
│   ├── client/
│   │   ├── __init__.py
│   │   └── cli.py                      # Typer CLI
│   └── models/
│       ├── __init__.py
│       └── schemas.py                  # Pydantic models
├── tests/
├── pyproject.toml
└── README.md
```

#### 1.2 Workflow Definitions

```python
# workflows/sandbox_orchestration.py
from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta

@workflow.defn
class SandboxOrchestrationWorkflow:
    """Main workflow that orchestrates parallel fork workflows."""

    @workflow.run
    async def run(self, config: OrchestrationConfig) -> OrchestrationResult:
        # Initialize state
        self.forks_completed = 0
        self.forks_failed = 0
        self.results = []

        # Launch fork workflows in parallel (with rate limiting)
        fork_handles = []
        for i in range(config.num_forks):
            # Rate limit: max N concurrent forks
            if len(fork_handles) >= config.max_concurrent:
                # Wait for one to complete before starting next
                done = await workflow.wait_condition(
                    lambda: self.forks_completed > len(fork_handles) - config.max_concurrent
                )

            # Start child workflow for this fork
            handle = await workflow.start_child_workflow(
                ForkWorkflow.run,
                ForkConfig(
                    fork_num=i + 1,
                    repo_url=config.repo_url,
                    branch=f"{config.branch}-{i+1}" if config.num_forks > 1 else config.branch,
                    prompt=config.prompt,
                    model=config.model,
                    timeout=config.fork_timeout,
                ),
                id=f"{workflow.info().workflow_id}-fork-{i+1}",
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=5),
                    backoff_coefficient=2.0,
                ),
            )
            fork_handles.append(handle)

        # Collect results
        for handle in fork_handles:
            try:
                result = await handle.result()
                self.results.append(result)
                self.forks_completed += 1
            except Exception as e:
                self.forks_failed += 1
                self.results.append(ForkResult(
                    status="failed",
                    error=str(e),
                ))

        return OrchestrationResult(
            total_forks=config.num_forks,
            successful=self.forks_completed,
            failed=self.forks_failed,
            results=self.results,
        )

    @workflow.signal
    async def cancel_fork(self, fork_num: int):
        """Signal to cancel a specific fork."""
        pass

    @workflow.query
    def get_progress(self) -> dict:
        """Query current progress."""
        return {
            "completed": self.forks_completed,
            "failed": self.forks_failed,
            "results": self.results,
        }
```

```python
# workflows/fork_workflow.py
@workflow.defn
class ForkWorkflow:
    """Workflow for a single fork execution with full durability."""

    @workflow.run
    async def run(self, config: ForkConfig) -> ForkResult:
        # 1. Create sandbox with retry
        sandbox_id = await workflow.execute_activity(
            create_sandbox,
            CreateSandboxInput(template="base", timeout=config.timeout),
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=2),
                backoff_coefficient=2.0,
                non_retryable_error_types=["AuthenticationError"],
            ),
        )

        try:
            # 2. Clone repository
            await workflow.execute_activity(
                execute_sandbox_command,
                CommandInput(
                    sandbox_id=sandbox_id,
                    command=f"git clone {config.repo_url} /workspace && cd /workspace && git checkout {config.branch}",
                ),
                start_to_close_timeout=timedelta(minutes=10),
            )

            # 3. Run Claude agent with heartbeat
            agent_result = await workflow.execute_activity(
                run_claude_agent,
                AgentInput(
                    sandbox_id=sandbox_id,
                    prompt=config.prompt,
                    model=config.model,
                    fork_num=config.fork_num,
                ),
                start_to_close_timeout=timedelta(hours=2),
                heartbeat_timeout=timedelta(minutes=5),  # Must heartbeat every 5 min
            )

            return ForkResult(
                status="success",
                sandbox_id=sandbox_id,
                cost=agent_result.cost,
                tokens=agent_result.tokens,
            )

        finally:
            # 4. Always cleanup sandbox
            await workflow.execute_activity(
                cleanup_sandbox,
                CleanupInput(sandbox_id=sandbox_id),
                start_to_close_timeout=timedelta(minutes=2),
            )
```

#### 1.3 Activity Definitions

```python
# activities/sandbox_activities.py
from temporalio import activity
from e2b import Sandbox
import asyncio

@activity.defn
async def create_sandbox(input: CreateSandboxInput) -> str:
    """Create E2B sandbox with health verification."""
    activity.heartbeat()

    sbx = await asyncio.to_thread(
        Sandbox.create,
        template=input.template,
        timeout=input.timeout,
    )

    # Verify sandbox is healthy
    info = await asyncio.to_thread(sbx.get_hostname)
    if not info:
        raise RuntimeError("Sandbox created but not responding")

    activity.logger.info(f"Created sandbox {sbx.sandbox_id}")
    return sbx.sandbox_id

@activity.defn
async def execute_sandbox_command(input: CommandInput) -> CommandResult:
    """Execute command in sandbox with heartbeat."""
    activity.heartbeat()

    sbx = Sandbox.connect(input.sandbox_id)
    result = sbx.commands.run(
        input.command,
        timeout=input.timeout or 300,
    )

    activity.heartbeat()

    return CommandResult(
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.exit_code,
    )

@activity.defn
async def run_claude_agent(input: AgentInput) -> AgentResult:
    """Run Claude SDK agent with periodic heartbeats."""
    from claude_code_sdk import ClaudeCodeSession

    async def run_with_heartbeat():
        # Start heartbeat task
        async def heartbeat_loop():
            while True:
                activity.heartbeat({"status": "running"})
                await asyncio.sleep(60)  # Heartbeat every minute

        heartbeat_task = asyncio.create_task(heartbeat_loop())

        try:
            # Run agent
            session = ClaudeCodeSession(
                sandbox_id=input.sandbox_id,
                model=input.model,
            )
            result = await session.run(input.prompt)
            return AgentResult(
                status="success",
                cost=result.cost,
                tokens=result.tokens,
                output=result.output,
            )
        finally:
            heartbeat_task.cancel()

    return await run_with_heartbeat()

@activity.defn
async def cleanup_sandbox(input: CleanupInput) -> None:
    """Kill sandbox, idempotent."""
    try:
        sbx = Sandbox.connect(input.sandbox_id)
        sbx.kill()
        activity.logger.info(f"Killed sandbox {input.sandbox_id}")
    except Exception as e:
        # Already dead, that's fine
        activity.logger.warning(f"Cleanup sandbox {input.sandbox_id}: {e}")
```

#### 1.4 Worker Setup

```python
# workers/sandbox_worker.py
from temporalio.client import Client
from temporalio.worker import Worker

async def main():
    client = await Client.connect("localhost:7233")

    worker = Worker(
        client,
        task_queue="sandbox-orchestration",
        workflows=[
            SandboxOrchestrationWorkflow,
            ForkWorkflow,
        ],
        activities=[
            create_sandbox,
            execute_sandbox_command,
            run_claude_agent,
            cleanup_sandbox,
            health_check_sandbox,
        ],
    )

    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
```

#### 1.5 CLI Integration

```python
# client/cli.py
import typer
from temporalio.client import Client

app = typer.Typer()

@app.command()
async def fork(
    repo_url: str,
    branch: str = "main",
    prompt: str = typer.Option(..., "--prompt", "-p"),
    num_forks: int = typer.Option(1, "--forks", "-f"),
    model: str = typer.Option("sonnet", "--model", "-m"),
    max_concurrent: int = typer.Option(5, "--max-concurrent"),
    timeout: int = typer.Option(7200, "--timeout"),  # 2 hours
):
    """Launch parallel sandbox forks with Temporal durability."""
    client = await Client.connect("localhost:7233")

    # Start workflow
    handle = await client.start_workflow(
        SandboxOrchestrationWorkflow.run,
        OrchestrationConfig(
            repo_url=repo_url,
            branch=branch,
            prompt=prompt,
            num_forks=num_forks,
            model=model,
            max_concurrent=max_concurrent,
            fork_timeout=timeout,
        ),
        id=f"sandbox-orch-{uuid.uuid4().hex[:8]}",
        task_queue="sandbox-orchestration",
    )

    typer.echo(f"Started workflow: {handle.id}")
    typer.echo(f"View in Temporal UI: http://localhost:8080/workflows/{handle.id}")

    # Wait for result
    result = await handle.result()

    # Display results table
    display_results(result)

@app.command()
def status(workflow_id: str):
    """Check status of a running workflow."""
    client = await Client.connect("localhost:7233")
    handle = client.get_workflow_handle(workflow_id)

    progress = await handle.query(SandboxOrchestrationWorkflow.get_progress)
    typer.echo(f"Progress: {progress}")

@app.command()
def resume(workflow_id: str):
    """Resume a workflow (Temporal handles this automatically)."""
    typer.echo(f"Workflow {workflow_id} will automatically resume from last checkpoint")
    typer.echo(f"View in Temporal UI: http://localhost:8080/workflows/{workflow_id}")
```

---

### Phase 2: Enhanced Observability

**Goal**: Add comprehensive monitoring, metrics, and dashboards

#### 2.1 Metrics Integration

```python
# observability/metrics.py
from temporalio.runtime import PrometheusConfig, Runtime, TelemetryConfig

def create_runtime_with_metrics() -> Runtime:
    """Create Temporal runtime with Prometheus metrics."""
    return Runtime(
        telemetry=TelemetryConfig(
            metrics=PrometheusConfig(bind_address="0.0.0.0:9090"),
        )
    )

# Custom metrics
from prometheus_client import Counter, Histogram, Gauge

SANDBOX_CREATED = Counter(
    "sandbox_created_total",
    "Total sandboxes created",
    ["template", "status"]
)

SANDBOX_DURATION = Histogram(
    "sandbox_duration_seconds",
    "Sandbox execution duration",
    ["fork_num", "status"],
    buckets=[60, 300, 600, 1800, 3600, 7200]
)

AGENT_COST = Histogram(
    "agent_cost_usd",
    "Claude agent cost per fork",
    ["model"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0]
)

ACTIVE_SANDBOXES = Gauge(
    "active_sandboxes",
    "Currently active sandboxes"
)
```

#### 2.2 Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Sandbox Orchestration",
    "panels": [
      {
        "title": "Active Workflows",
        "type": "stat",
        "targets": [
          {
            "expr": "temporal_workflow_active_count{namespace=\"default\", workflow_type=\"SandboxOrchestrationWorkflow\"}"
          }
        ]
      },
      {
        "title": "Fork Success Rate",
        "type": "gauge",
        "targets": [
          {
            "expr": "rate(temporal_workflow_completed_count{workflow_type=\"ForkWorkflow\"}[5m]) / rate(temporal_workflow_started_count{workflow_type=\"ForkWorkflow\"}[5m]) * 100"
          }
        ]
      },
      {
        "title": "Sandbox Duration Distribution",
        "type": "histogram",
        "targets": [
          {
            "expr": "sandbox_duration_seconds_bucket"
          }
        ]
      },
      {
        "title": "Agent Cost Over Time",
        "type": "timeseries",
        "targets": [
          {
            "expr": "sum(rate(agent_cost_usd_sum[5m])) by (model)"
          }
        ]
      },
      {
        "title": "Activity Retries",
        "type": "timeseries",
        "targets": [
          {
            "expr": "rate(temporal_activity_execution_failed_count[5m])"
          }
        ]
      }
    ]
  }
}
```

#### 2.3 Structured Logging

```python
# observability/logging.py
import structlog
from temporalio import activity, workflow

def configure_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

# Usage in activities
@activity.defn
async def create_sandbox(input: CreateSandboxInput) -> str:
    log = structlog.get_logger().bind(
        activity="create_sandbox",
        workflow_id=activity.info().workflow_id,
        template=input.template,
    )

    log.info("creating_sandbox")

    try:
        sandbox_id = await _create_sandbox(input)
        log.info("sandbox_created", sandbox_id=sandbox_id)
        return sandbox_id
    except Exception as e:
        log.error("sandbox_creation_failed", error=str(e), exc_info=True)
        raise
```

---

### Phase 3: Advanced Features

**Goal**: Add workflow queries, signals, and scheduled operations

#### 3.1 Live Progress Monitoring

```python
# Add to SandboxOrchestrationWorkflow
@workflow.query
def get_detailed_status(self) -> DetailedStatus:
    """Get detailed status including per-fork progress."""
    return DetailedStatus(
        workflow_id=workflow.info().workflow_id,
        started_at=self.started_at,
        forks_total=self.total_forks,
        forks_completed=self.forks_completed,
        forks_failed=self.forks_failed,
        forks_in_progress=[f for f in self.fork_states if f.status == "running"],
        estimated_completion=self._estimate_completion(),
        total_cost=sum(r.cost for r in self.results if r.cost),
    )

@workflow.signal
def pause_workflow(self):
    """Signal to pause accepting new forks."""
    self.paused = True

@workflow.signal
def resume_workflow(self):
    """Signal to resume workflow."""
    self.paused = False
```

#### 3.2 Scheduled Cleanup Workflow

```python
# workflows/cleanup_workflow.py
@workflow.defn
class ScheduledCleanupWorkflow:
    """Periodically clean up orphaned sandboxes."""

    @workflow.run
    async def run(self):
        while True:
            # Find orphaned sandboxes (running but no active workflow)
            orphans = await workflow.execute_activity(
                find_orphaned_sandboxes,
                start_to_close_timeout=timedelta(minutes=5),
            )

            for sandbox_id in orphans:
                await workflow.execute_activity(
                    cleanup_sandbox,
                    CleanupInput(sandbox_id=sandbox_id),
                    start_to_close_timeout=timedelta(minutes=2),
                )

            # Run every 15 minutes
            await workflow.sleep(timedelta(minutes=15))
```

#### 3.3 Cost Budget Enforcement

```python
# Add to ForkWorkflow
@workflow.run
async def run(self, config: ForkConfig) -> ForkResult:
    # Check budget before starting
    current_spend = await workflow.execute_activity(
        get_current_spend,
        start_to_close_timeout=timedelta(seconds=30),
    )

    if current_spend >= config.budget_limit:
        return ForkResult(
            status="budget_exceeded",
            error=f"Budget limit ${config.budget_limit} exceeded",
        )

    # ... rest of workflow

    # Monitor cost during execution
    @workflow.signal
    def update_cost(self, cost: float):
        self.current_cost = cost
        if self.current_cost > config.budget_limit:
            self.should_cancel = True
```

---

## Deployment Architecture

### Option 1: Temporal Cloud (Recommended for Production)

```yaml
# temporal-cloud-config.yaml
namespace: sandbox-orchestration
connection:
  address: your-namespace.tmprl.cloud:7233
  tls:
    client_cert_path: /certs/client.pem
    client_key_path: /certs/client.key
```

**Pros**: Fully managed, auto-scaling, 99.99% SLA
**Cost**: ~$200/mo base + usage

### Option 2: Self-Hosted Temporal

```yaml
# docker-compose.yaml
version: '3.8'
services:
  temporal:
    image: temporalio/auto-setup:1.24
    ports:
      - "7233:7233"
    environment:
      - DB=postgresql
      - DB_PORT=5432
      - POSTGRES_USER=temporal
      - POSTGRES_PWD=temporal
      - POSTGRES_SEEDS=postgresql
    depends_on:
      - postgresql

  temporal-ui:
    image: temporalio/ui:2.26
    ports:
      - "8080:8080"
    environment:
      - TEMPORAL_ADDRESS=temporal:7233

  postgresql:
    image: postgres:15
    environment:
      - POSTGRES_USER=temporal
      - POSTGRES_PASSWORD=temporal
    volumes:
      - temporal-db:/var/lib/postgresql/data

  worker:
    build: ./apps/sandbox_temporal
    command: python -m src.workers.sandbox_worker
    environment:
      - TEMPORAL_ADDRESS=temporal:7233
      - E2B_API_KEY=${E2B_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - temporal

  prometheus:
    image: prom/prometheus:v2.47.0
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:10.1.0
    ports:
      - "3000:3000"
    volumes:
      - ./grafana/dashboards:/var/lib/grafana/dashboards

volumes:
  temporal-db:
```

---

## Migration Plan

### Week 1-2: Foundation

1. Set up Temporal development environment (docker-compose)
2. Create `apps/sandbox_temporal/` structure
3. Implement basic workflows and activities
4. Write unit tests with Temporal test framework

### Week 3-4: Integration

1. Integrate E2B SDK into activities
2. Integrate Claude SDK into activities
3. Implement retry policies and timeouts
4. Add heartbeating to long-running activities

### Week 5-6: Observability

1. Set up Prometheus metrics collection
2. Create Grafana dashboards
3. Implement structured logging
4. Add cost tracking and budget alerts

### Week 7-8: Production Hardening

1. Load testing with 50+ concurrent forks
2. Chaos testing (kill workers, network partitions)
3. Documentation and runbooks
4. Deploy to Temporal Cloud or self-hosted production

---

## Benefits Summary

| Benefit | Before | After |
|---------|--------|-------|
| **Durability** | Process crash = total loss | Automatic resume from checkpoint |
| **Retry** | None | 3 attempts with exponential backoff |
| **Rate Limiting** | None | Configurable max concurrent |
| **Observability** | File logs | Web UI + Prometheus + Grafana |
| **Health Checks** | None | Pre-execution + heartbeat |
| **Cost Tracking** | Basic | Real-time with budget enforcement |
| **Scalability** | Single machine | Distributed workers |
| **Debugging** | Read log files | Replay execution in UI |

---

## Alternative: Motia.dev Implementation

If a lighter-weight solution is preferred, Motia.dev offers:

```typescript
// motia-sandbox.ts
import { step, emit, state } from 'motia';

// Define sandbox orchestration as steps
export const createSandboxStep = step('create-sandbox', async (input) => {
  const sandbox = await e2b.Sandbox.create(input.template);
  await state.set(`sandbox:${input.forkNum}`, sandbox.id);
  await emit('sandbox-created', { sandboxId: sandbox.id, forkNum: input.forkNum });
});

export const runAgentStep = step('run-agent', async (input) => {
  const sandboxId = await state.get(`sandbox:${input.forkNum}`);
  const result = await runClaudeAgent(sandboxId, input.prompt);
  await emit('agent-completed', { forkNum: input.forkNum, result });
});

// Automatic retry on failure, state persisted across crashes
```

**Tradeoffs**:
- (+) Simpler mental model (Steps instead of Workflows/Activities)
- (+) Unified with API layer if building web interfaces
- (-) Less mature than Temporal
- (-) Fewer production deployments at scale
- (-) TypeScript-first (Python SDK coming)

---

## Conclusion

Temporal.io is the recommended solution for enhancing sandbox durability and observability at scale. Its proven track record at OpenAI for image generation workloads, combined with its mature Python SDK and comprehensive observability features, makes it the ideal choice for production-grade sandbox orchestration.

The implementation plan provides a clear path from the current in-memory orchestration to a fully durable, observable, and scalable system that can handle hundreds of concurrent sandbox forks with automatic retry, checkpoint/resume, and real-time monitoring.

---

## Sources

- [Temporal.io - Durable Execution Solutions](https://temporal.io/)
- [Temporal for AI](https://temporal.io/solutions/ai)
- [Temporal Blog - Durable Execution in Distributed Systems](https://temporal.io/blog/durable-execution-in-distributed-systems-increasing-observability)
- [From AI Hype to Durable Reality](https://temporal.io/blog/from-ai-hype-to-durable-reality-why-agentic-flows-need-distributed-systems)
- [OpenAI Agents SDK Integration with Temporal](https://docs.temporal.io/ai-cookbook/durable-agent-with-tools)
- [Temporal Agents with Knowledge Graphs - OpenAI Cookbook](https://cookbook.openai.com/examples/partners/temporal_agents_with_knowledge_graphs/temporal_agents_with_knowledge_graphs)
- [Motia.dev Documentation](https://www.motia.dev/docs)
- [Motia GitHub](https://github.com/MotiaDev/motia)
- [Introducing Motia - Deep Dive](https://www.neatprompts.com/p/motia-deep-dive)
