# Sandbox Temporal

Durable sandbox orchestration using [Temporal.io](https://temporal.io/) for reliable, scalable parallel agent execution.

## Features

- **Durable Execution**: Automatic checkpoint/resume - workflows survive crashes
- **Parallel Forks**: Run N sandbox forks concurrently with rate limiting
- **Retry Policies**: Exponential backoff on transient failures
- **Health Checks**: Verify sandbox health before agent execution
- **Budget Enforcement**: Stop workflows when cost limits are reached
- **Observability**: Prometheus metrics, structured logging, Temporal UI

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 SandboxOrchestrationWorkflow                │
│  • Rate-limited parallel fork execution                     │
│  • Progress queries, pause/resume/cancel signals            │
└──────────────────────────┬──────────────────────────────────┘
                           │ spawns
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │ ForkWorkflow│ │ ForkWorkflow│ │ ForkWorkflow│
    │   (Fork 1)  │ │   (Fork 2)  │ │   (Fork N)  │
    └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
           │               │               │
           ▼               ▼               ▼
    ┌─────────────────────────────────────────────────────────┐
    │                    Activities                           │
    │  • create_sandbox()    • run_claude_agent()             │
    │  • execute_command()   • cleanup_sandbox()              │
    │  • health_check()      • record_metrics()               │
    └─────────────────────────────────────────────────────────┘
```

## Installation

```bash
cd apps/sandbox_temporal
uv sync
```

## Quick Start

### 1. Start Temporal Server (Docker)

```bash
# From repository root
docker-compose -f docker/temporal-compose.yaml up -d
```

### 2. Start Worker

```bash
uv run sandbox-worker
```

### 3. Launch Forks

```bash
# Single fork
uv run sandbox-temporal fork https://github.com/user/repo \
  --prompt "Implement feature X"

# Multiple forks
uv run sandbox-temporal fork https://github.com/user/repo \
  --branch main \
  --prompt "Refactor the authentication module" \
  --forks 5 \
  --model opus \
  --max-concurrent 3 \
  --budget 10.0
```

## CLI Commands

### `fork` - Launch Sandbox Forks

```bash
uv run sandbox-temporal fork <repo-url> [OPTIONS]

Options:
  -b, --branch TEXT          Git branch [default: main]
  -p, --prompt TEXT          Prompt for agents [required]
  -f, --forks INTEGER        Number of forks [default: 1]
  -m, --model TEXT           Claude model [default: sonnet]
  --max-concurrent INTEGER   Max concurrent forks [default: 5]
  -t, --timeout INTEGER      Timeout per fork (seconds) [default: 7200]
  --budget FLOAT             Budget limit (USD)
  --wait/--no-wait           Wait for completion [default: wait]
```

### `status` - Check Workflow Progress

```bash
uv run sandbox-temporal status <workflow-id>
```

### `cancel` - Cancel Workflow

```bash
uv run sandbox-temporal cancel <workflow-id>
```

### `pause` / `resume` - Control Workflow

```bash
uv run sandbox-temporal pause <workflow-id>
uv run sandbox-temporal resume <workflow-id>
```

### `list` - List Running Workflows

```bash
uv run sandbox-temporal list --limit 20
```

### `cleanup` - Start Cleanup Workflow

```bash
# Start orphaned sandbox cleanup (runs continuously)
uv run sandbox-temporal cleanup --interval 15 --max-age 180

# Stop cleanup
uv run sandbox-temporal stop-cleanup
```

## Environment Variables

```bash
# Required
E2B_API_KEY=your_e2b_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Temporal Connection
TEMPORAL_ADDRESS=localhost:7233        # Default
TEMPORAL_NAMESPACE=default             # Default
TEMPORAL_TASK_QUEUE=sandbox-orchestration

# Optional: Temporal Cloud TLS
TEMPORAL_TLS_CERT=/path/to/client.pem
TEMPORAL_TLS_KEY=/path/to/client.key

# Optional: GitHub
GITHUB_TOKEN=your_github_token

# Optional: Metrics
METRICS_PORT=9090
DISABLE_METRICS=false
```

## Temporal Cloud

For production, use Temporal Cloud:

```bash
export TEMPORAL_ADDRESS=your-namespace.tmprl.cloud:7233
export TEMPORAL_NAMESPACE=your-namespace
export TEMPORAL_TLS_CERT=/path/to/client.pem
export TEMPORAL_TLS_KEY=/path/to/client.key

uv run sandbox-worker
```

## Monitoring

### Temporal Web UI

Access at `http://localhost:8080` to:
- View workflow executions
- Inspect event history
- Debug failures with replay
- Send signals (pause/resume/cancel)

### Prometheus Metrics

Worker exposes metrics at `http://localhost:9090/metrics`:

- `sandbox_fork_completed_total{status, model}`
- `sandbox_fork_duration_seconds{status}`
- `sandbox_fork_cost_usd{model}`
- Temporal SDK metrics (workflow/activity counts, latencies)

### Grafana Dashboards

Import dashboards from `docker/grafana/dashboards/`:
- `sandbox-orchestration.json` - Fork execution metrics
- `temporal-sdk.json` - Temporal SDK metrics

## Development

### Run Tests

```bash
uv run pytest -v

# With coverage
uv run pytest --cov=src --cov-report=html
```

### Local Development Without Temporal

For testing activities without full Temporal setup:

```python
from src.activities import create_sandbox, run_claude_agent

# Test activity directly
result = await create_sandbox("base", 300)
print(result)
```

## Workflow Details

### SandboxOrchestrationWorkflow

Main workflow that:
1. Validates configuration
2. Launches fork workflows with rate limiting
3. Collects results and aggregates costs
4. Supports pause/resume/cancel signals
5. Provides progress queries

### ForkWorkflow

Per-fork workflow that:
1. Checks budget constraints
2. Creates E2B sandbox (with retry)
3. Runs health check
4. Executes Claude agent (with heartbeat)
5. Always cleans up sandbox

### ScheduledCleanupWorkflow

Background workflow that:
1. Periodically scans for orphaned sandboxes
2. Cleans up sandboxes with no workflow association
3. Runs until explicitly stopped

## Retry Policies

| Activity | Max Attempts | Initial Interval | Backoff |
|----------|--------------|------------------|---------|
| create_sandbox | 3 | 5s | 2x |
| run_claude_agent | 2 | 10s | 2x |
| cleanup_sandbox | 3 | 2s | 2x |
| health_check | 1 | - | - |

Non-retryable errors:
- `SandboxCreationError` (auth failures)
- `AgentBudgetExceededError`
- `AgentTimeoutError`

## License

MIT
