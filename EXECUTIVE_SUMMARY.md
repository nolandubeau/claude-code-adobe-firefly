# Executive Summary: Claude Code Adobe Firefly + Agent Sandboxes

**For Forward Deployed Agentic Engineers**

---

## TL;DR

This repository is a **production-ready Claude Code plugin** that combines:

1. **Adobe Firefly MCP Server** - AI image generation/manipulation via tool calls
2. **E2B Agent Sandboxes** - Isolated, scalable environments for parallel agent execution
3. **UX Design Skills** - Bencium design skills for consistent UI/UX output

**Result:** Agents can generate imagery, design interfaces, and execute tasks at scale—all in isolated, safe environments.

---

## Why This Matters for Agentic Engineering

### The Problem

Traditional agent deployments face three constraints:

| Constraint | Impact |
|------------|--------|
| **Safety** | Agents with file/code access risk production systems |
| **Scale** | Sequential task execution limits throughput |
| **Capability** | Text-only agents can't produce visual assets |

### The Solution

```
┌─────────────────────────────────────────────────────────────────┐
│  Claude Code Agent                                              │
│  ├── MCP Tools: Firefly image generation                        │
│  ├── Skills: Bencium UX design guidance                         │
│  └── Sandboxes: E2B isolated execution environments             │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐    ┌──────────┐    ┌──────────┐
        │ Sandbox  │    │ Sandbox  │    │ Sandbox  │
        │ Fork 1   │    │ Fork 2   │    │ Fork N   │
        │          │    │          │    │          │
        │ • Claude │    │ • Claude │    │ • Claude │
        │ • Firefly│    │ • Firefly│    │ • Firefly│
        │ • Full   │    │ • Full   │    │ • Full   │
        │   agency │    │   agency │    │   agency │
        └──────────┘    └──────────┘    └──────────┘
```

---

## Core Capabilities

### 1. Adobe Firefly MCP Server (Python/FastMCP)

Six tools exposed via MCP for multimodal content creation:

| Tool | Use Case |
|------|----------|
| `generate_image` | Text-to-image with style control |
| `expand_image` | Extend canvas beyond boundaries |
| `fill_image` | Inpaint/replace regions with masks |
| `remove_background` | Extract subjects from backgrounds |
| `generate_similar_images` | Create variations from reference |
| `apply_style_transfer` | Apply visual style from reference |

**Key Parameters:** `seed` (reproducibility), `aspect_ratio`, `style_options`, `structure`

```bash
# Install MCP server
cd apps/firefly_mcp && uv sync
uv run mcp install server.py --name "Adobe Firefly"
```

### 2. E2B Agent Sandboxes

Isolated cloud environments where agents have full control:

| Component | Purpose |
|-----------|---------|
| `sandbox_workflows/` | **obox**: Parallel agent forks |
| `sandbox_mcp/` | MCP server for LLM integration |
| `sandbox_cli/` | Direct sandbox management |
| `cc_in_sandbox/` | Run Claude Code inside sandbox |

**Value Proposition:**

- **Isolation**: Each fork is a separate VM—no risk to production
- **Scale**: Run N parallel agents, each with full agency
- **Agency**: Install packages, modify files, run commands, push to git

```bash
# Launch 4 parallel agent forks
uv run obox https://github.com/org/repo.git \
  --branch feature \
  --model opus \
  --forks 4 \
  --prompt "Implement feature X with different approaches"
```

### 3. Bencium UX Design Skills

Two Claude Code skills for consistent design output:

| Skill | Behavior | Best For |
|-------|----------|----------|
| `bencium-controlled-ux-designer` | Asks before decisions, systematic | Production, enterprise |
| `bencium-innovative-ux-designer` | Commits boldly, breaks patterns | Landing pages, campaigns |

Both avoid "AI slop"—generic Inter fonts, SaaS blue, glassmorphism.

---

## Deployment Patterns

### Pattern 1: Single Agent + Multimodal Output

Agent generates both code and imagery in one session.

```
User: "Create a dashboard with custom illustrations"
Agent:
  1. Uses bencium-controlled skill for layout
  2. Calls Firefly generate_image for illustrations
  3. Builds React components with generated assets
```

### Pattern 2: Parallel Design Exploration

Launch multiple agents to explore different directions simultaneously.

```
User: "Design 4 onboarding variations"
Orchestrator:
  1. Spawns 4 sandbox forks
  2. Each fork: different design direction + Firefly imagery
  3. Aggregates results for comparison
  4. Stakeholder picks winner
```

**Time savings:** 4 hours → 1 hour

### Pattern 3: Batch Processing Pipeline

Scale image processing across sandbox fleet.

```
User: "Process 500 product images"
Pipeline:
  1. Distributes 50 products per sandbox (10 forks)
  2. Each sandbox: remove_background → generate backgrounds → resize
  3. Aggregates to CDN
```

**Time savings:** 17 hours → 1.7 hours

### Pattern 4: A/B Variant Generation

Generate all test variants in parallel.

```
Matrix: 2 styles × 2 colors × 2 layouts = 8 variants
→ 8 sandbox forks, each produces complete landing page
→ Deploy all to A/B testing infrastructure
```

---

## Architecture Overview

```
claude-code-adobe-firefly/
├── apps/
│   ├── firefly_mcp/          # MCP server (Python/FastMCP)
│   ├── firefly_sdk/          # SDK + Typer CLI + mock testing
│   ├── sandbox_workflows/    # obox: parallel fork orchestration
│   ├── sandbox_mcp/          # MCP server for sandbox control
│   └── sandbox_cli/          # Direct CLI for E2B
├── .claude/
│   ├── agents/adobe-firefly/ # Specialized agents
│   ├── commands/adobe-firefly/ # Slash commands
│   └── skills/               # Bencium + Firefly skills
└── docs/examples/            # Integration patterns
```

---

## Quick Start

### Prerequisites

```bash
# Required
FIREFLY_CLIENT_ID=...      # Adobe Developer Console
FIREFLY_CLIENT_SECRET=...  # OAuth Server-to-Server
E2B_API_KEY=...            # e2b.dev
ANTHROPIC_API_KEY=...      # console.anthropic.com
```

### Install Firefly MCP

```bash
cd apps/firefly_mcp
uv sync
uv run mcp install server.py --name "Adobe Firefly"
```

### Test with Mock Mode (No Credentials)

```bash
cd apps/firefly_sdk
uv sync
firefly generate "test prompt" --use-mocks --verbose
```

### Run Parallel Sandbox Workflow

```bash
cd apps/sandbox_workflows
uv sync
uv run obox <repo-url> --forks 4 --model opus --prompt "Your task"
```

---

## Test Coverage

| Component | Tests | Coverage |
|-----------|-------|----------|
| Firefly SDK | 99 | CLI, client, models |
| Firefly MCP | 27 | All 6 tools, error handling |
| **Total** | **126** | Full mock infrastructure |

```bash
# Run all tests
cd apps/firefly_sdk && uv run pytest --cov=firefly_sdk
cd apps/firefly_mcp && uv run pytest --cov
```

---

## Key Differentiators

| Feature | This Repo | Alternatives |
|---------|-----------|--------------|
| **Multimodal** | Firefly MCP tools | Text-only agents |
| **Isolation** | E2B sandboxes | Local execution risk |
| **Scale** | Parallel forks | Sequential processing |
| **Design Quality** | Bencium skills | Generic AI output |
| **Reproducibility** | Seed parameters | Non-deterministic |
| **Testing** | Mock mode, 126 tests | Manual testing |

---

## Production Considerations

### Rate Limits

- Firefly API: Respect Adobe rate limits
- E2B: Concurrent sandbox limits per plan
- Stagger fork launches: `sleep 5` between spawns

### Cost Model

| Resource | Cost Factor |
|----------|-------------|
| Firefly API calls | Per-image pricing |
| E2B sandbox time | Per-minute compute |
| Claude API | Per-token (model-dependent) |

**Optimization:** Use `--model haiku` for simple tasks, `opus` for complex reasoning.

### Security

- Sandboxes are isolated VMs—no access to host
- Credentials injected via environment variables
- Git operations use scoped tokens

---

## Example Use Cases

| Industry | Use Case | Components |
|----------|----------|------------|
| **E-commerce** | Product catalog processing | Firefly remove_background + sandboxes |
| **Marketing** | A/B landing page generation | Bencium + Firefly + parallel forks |
| **Branding** | Identity exploration | 5 parallel brand system generations |
| **SaaS** | Feature prototyping | Design skills + generated illustrations |
| **Agency** | Client presentations | Multiple creative directions at once |

---

## Next Steps

1. **Clone & Configure**
   ```bash
   git clone https://github.com/nolandubeau/claude-code-adobe-firefly.git
   cp .env.example .env  # Add credentials
   ```

2. **Start with Fundamentals**
   ```bash
   cd apps/sandbox_fundamentals
   uv sync && uv run python 01_basic_sandbox.py
   ```

3. **Run Scaled Example**
   ```bash
   cd apps/sandbox_workflows
   uv run obox <your-repo> --forks 4 --prompt "Your task"
   ```

4. **Review Integration Examples**
   - `docs/examples/05-parallel-design-exploration.md`
   - `docs/examples/06-ab-landing-page-scale.md`

---

## Support

- **Issues:** https://github.com/nolandubeau/claude-code-adobe-firefly/issues
- **Adobe Firefly Docs:** https://developer.adobe.com/firefly-services/docs/
- **E2B Docs:** https://e2b.dev/docs
- **Claude Code Docs:** https://docs.anthropic.com/claude-code

---

**Bottom Line:** This repo gives your agents eyes (Firefly), hands (sandboxes), and taste (Bencium)—at scale.
