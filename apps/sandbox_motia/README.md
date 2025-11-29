# Sandbox Motia

Durable sandbox orchestration using [Motia.dev](https://www.motia.dev/) - a unified backend framework for APIs, events, and AI agents.

## Features

- **Event-Driven Architecture**: Steps communicate via events with automatic retry
- **Unified State**: Shared key-value store across all steps
- **Fault Tolerance**: Built-in error handling without manual queue setup
- **Observability**: Full execution traces with step timelines and logs
- **TypeScript-First**: Type-safe step definitions with Zod schemas

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Event Flow                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  orchestration-requested                                    │
│          │                                                  │
│          ▼                                                  │
│    [orchestrate] ──────► fork-started (×N)                  │
│                               │                             │
│                               ▼                             │
│                        [create-sandbox]                     │
│                               │                             │
│               ┌───────────────┼───────────────┐             │
│               ▼               │               ▼             │
│       sandbox-created         │    sandbox-creation-failed  │
│               │               │               │             │
│               ▼               │               │             │
│        [health-check]         │               │             │
│               │               │               │             │
│       ┌───────┴───────┐       │               │             │
│       ▼               ▼       │               │             │
│ health-passed   health-failed │               │             │
│       │               │       │               │             │
│       ▼               │       │               │             │
│   [run-agent]         │       │               │             │
│       │               │       │               │             │
│   ┌───┴───┐           │       │               │             │
│   ▼       ▼           │       │               │             │
│ agent-   agent-       │       │               │             │
│ completed failed      │       │               │             │
│   │       │           │       │               │             │
│   └───┬───┘           │       │               │             │
│       ▼               ▼       ▼               ▼             │
│ [record-metrics] + [cleanup-sandbox]                        │
│                       │                                     │
│                       ▼                                     │
│               sandbox-cleaned                               │
│                       │                                     │
│                       ▼                                     │
│              [check-completion]                             │
│                       │                                     │
│                       ▼                                     │
│           orchestration-completed                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Installation

```bash
cd apps/sandbox_motia
npm install
```

## Quick Start

### 1. Start Motia Development Server

```bash
npm run dev
```

### 2. Trigger Orchestration

```typescript
import { emit } from 'motia';

await emit('orchestration-requested', {
  workflowId: 'my-workflow-123',
  repoUrl: 'https://github.com/user/repo',
  branch: 'main',
  prompt: 'Implement feature X',
  numForks: 5,
  model: 'sonnet',
  maxConcurrent: 3,
});
```

### 3. Monitor in Workbench

Open `http://localhost:3000` to view:
- Live event traces
- Step execution timelines
- State operations
- Logs and errors

## Project Structure

```
sandbox_motia/
├── src/
│   ├── index.ts              # Main exports
│   ├── steps/                # Step definitions
│   │   ├── create-sandbox.step.ts
│   │   ├── run-agent.step.ts
│   │   ├── cleanup-sandbox.step.ts
│   │   ├── health-check.step.ts
│   │   ├── orchestrate.step.ts
│   │   └── record-metrics.step.ts
│   ├── flows/                # Flow definitions
│   │   └── sandbox-orchestration.flow.ts
│   └── state/                # State schemas
│       └── index.ts
├── tests/                    # Test files
├── package.json
└── tsconfig.json
```

## Steps

### `orchestrate`
- **Subscribes**: `orchestration-requested`
- **Emits**: `fork-started`
- **Description**: Initializes orchestration state and emits fork-started events

### `create-sandbox`
- **Subscribes**: `fork-started`
- **Emits**: `sandbox-created`, `sandbox-creation-failed`
- **Description**: Creates E2B sandbox for a fork

### `health-check`
- **Subscribes**: `sandbox-created`
- **Emits**: `health-check-passed`, `health-check-failed`
- **Description**: Verifies sandbox is healthy before agent execution

### `run-agent`
- **Subscribes**: `sandbox-created` (after health check)
- **Emits**: `agent-completed`, `agent-failed`
- **Description**: Executes Claude Code agent in sandbox

### `record-metrics`
- **Subscribes**: `agent-completed`, `agent-failed`
- **Emits**: `metrics-recorded`
- **Description**: Records execution metrics and costs

### `cleanup-sandbox`
- **Subscribes**: `agent-completed`, `agent-failed`
- **Emits**: `sandbox-cleaned`
- **Description**: Kills sandbox after fork completion

### `check-completion`
- **Subscribes**: `sandbox-cleaned`
- **Emits**: `orchestration-completed`
- **Description**: Checks if all forks are done

## State Management

Motia provides a unified key-value state store:

```typescript
// Get state
const forkState = await state.get<ForkState>(
  STATE_KEYS.fork(workflowId, forkNum)
);

// Set state
await state.set(STATE_KEYS.fork(workflowId, forkNum), {
  status: 'running',
  sandboxId: sandbox.sandboxId,
});
```

### State Keys

| Key Pattern | Description |
|-------------|-------------|
| `orchestration:{workflowId}` | Main orchestration state |
| `fork:{workflowId}:{forkNum}` | Per-fork execution state |
| `sandbox:{sandboxId}` | Sandbox reference data |
| `metrics:{workflowId}` | Aggregated metrics |

## Environment Variables

```bash
# Required
E2B_API_KEY=your_e2b_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Optional
GITHUB_TOKEN=your_github_token
MOTIA_PORT=3000
MOTIA_LOG_LEVEL=info
```

## Configuration

### Flow Configuration

```typescript
const flow = createSandboxOrchestrationFlow({
  maxConcurrent: 10,    // Max parallel step executions
  retryAttempts: 5,     // Max retry attempts per step
});
```

### Retry Policy

Default retry configuration:
- Max attempts: 3
- Initial delay: 1s
- Backoff multiplier: 2x
- Max delay: 30s

### Rate Limiting

Default rate limiting:
- Max concurrent: 5 steps
- Window: 1000ms

## Development

### Run Tests

```bash
npm test
```

### Type Check

```bash
npm run typecheck
```

### Build

```bash
npm run build
```

## Comparison with Temporal

| Feature | Motia | Temporal |
|---------|-------|----------|
| Language | TypeScript-first | Multi-language |
| Abstraction | Steps + Events | Workflows + Activities |
| State | Built-in KV store | Event sourcing |
| Setup | Zero config | Requires server |
| Best for | Unified backend | Complex orchestration |

Choose Motia when:
- You want a unified backend (APIs + workflows + agents)
- You prefer TypeScript-first development
- You want simpler operational model

Choose Temporal when:
- You need proven scale (millions of workflows)
- You need multi-language support
- You need detailed event sourcing

## License

MIT
