# Adobe Firefly + Agent Sandboxes Plugin

This repository provides a comprehensive Claude Code plugin combining Adobe Firefly's AI-powered image generation with E2B Agent Sandboxes for scalable agentic engineering.

## Project Structure

```text
claude-code-adobe-firefly/
├── .claude/                    # Claude Code configuration
│   ├── commands/               # Slash commands
│   │   └── adobe-firefly/      # Adobe Firefly commands
│   │       ├── firefly-generate.md
│   │       ├── firefly-edit.md
│   │       ├── firefly-workflow.md
│   │       └── firefly-batch.md
│   ├── agents/                 # Specialized agents
│   │   └── adobe-firefly/      # Adobe Firefly agents
│   │       ├── firefly-creative.md
│   │       ├── firefly-editor.md
│   │       └── firefly-workflow.md
│   ├── skills/                 # Reusable skills
│   │   ├── adobe-firefly/      # Adobe Firefly skills
│   │   │   ├── firefly-api.md
│   │   │   └── firefly-prompts.md
│   │   ├── bencium-controlled-ux-designer/
│   │   └── bencium-innovative-ux-designer/
│   └── settings.json           # Plugin and MCP server config
├── apps/                       # Python applications
│   ├── firefly_mcp/            # MCP server for Firefly (Python/FastMCP)
│   ├── firefly_sdk/            # Python SDK with Typer CLI + mock testing
│   ├── firefly_examples/       # Standalone UV scripts
│   ├── sandbox_workflows/      # obox: Parallel agent forks
│   ├── sandbox_mcp/            # MCP server for sandboxes
│   ├── sandbox_cli/            # CLI for E2B management
│   ├── sandbox_fundamentals/   # E2B learning examples
│   ├── cc_in_sandbox/          # Claude Code in sandbox (ibox)
│   └── sandbox_agent_working_dir/
├── docs/                       # Documentation and examples
│   ├── README.md               # Skills documentation
│   ├── prompts.md
│   └── examples/               # Integration examples
└── README.md                   # Project documentation
```

---

## Adobe Firefly MCP Tools

The Adobe Firefly MCP server exposes these tools:

| Tool | Description |
|------|-------------|
| `generate_image` | Generate images from text prompts |
| `expand_image` | Extend images beyond boundaries (generative expand) |
| `fill_image` | Replace portions using masks (generative fill) |
| `remove_background` | Automatic background removal |
| `generate_similar_images` | Create variations from reference |
| `apply_style_transfer` | Apply artistic styles |

## Firefly Commands

- `/firefly-generate` - Quick image generation with customizable parameters
- `/firefly-edit` - Image editing (expand, fill, remove-bg, similar, style)
- `/firefly-workflow` - Multi-step creative workflows
- `/firefly-batch` - Batch image processing

## Firefly Agents

- `firefly-creative` - Creative image generation (subagent_type: firefly-creative)
- `firefly-editor` - Image editing and manipulation
- `firefly-workflow` - Multi-step workflow orchestration

---

## Agent Sandboxes (E2B)

Isolated, scalable sandbox environments for parallel agent experiments.

### Value Proposition

- **Isolation**: Each agent fork runs in a fully isolated E2B sandbox
- **Scale**: Run as many agent forks as needed, each independent
- **Agency**: Full control over sandbox environment

### Sandbox Apps

| App | Description |
|-----|-------------|
| `sandbox_workflows/` | **obox**: Parallel agent forks in isolated sandboxes |
| `sandbox_mcp/` | MCP server for LLM sandbox integration |
| `sandbox_cli/` | Click CLI for E2B management |
| `sandbox_fundamentals/` | E2B SDK learning examples |
| `cc_in_sandbox/` | Run Claude Code inside sandbox (ibox) |

### Sandbox Commands

```bash
# Initialize sandbox
uv run python src/main.py init

# Create with custom template
uv run python src/main.py sandbox create --template agent-sandbox-dev-node22

# Execute command
uv run python src/main.py exec <sandbox-id> "ls -la"

# Run parallel experiments (obox)
uv run obox <repo-url> --branch <branch> --model opus --prompt "task" --forks 3
```

---

## Skills

### Adobe Firefly Skills

- `firefly-api` - Core API interaction patterns and tool documentation
- `firefly-prompts` - Expert prompt engineering for image generation

### Bencium UX Designer Skills

- `bencium-controlled-ux-designer` - Systematic design for production work
- `bencium-innovative-ux-designer` - Bold creative design

## Bencium + Firefly Integration

See `docs/examples/` for detailed integration patterns:

| Example | Description |
|---------|-------------|
| `01-saas-landing-page.md` | SaaS page with AI-generated hero imagery |
| `02-product-showcase.md` | E-commerce with product photography pipeline |
| `03-creative-portfolio.md` | Agency portfolio with layered visuals |
| `04-dashboard-app.md` | Dashboard with custom illustrations |

### Example Workflows

1. **App Design with Generated Hero Images**
   - Use `bencium-innovative-ux-designer` to design the page layout
   - Use `/firefly-generate` to create hero imagery matching the design aesthetic
   - Integrate generated images into the final design

2. **Product Landing Page**
   - Use `bencium-controlled-ux-designer` for accessible, production-ready layouts
   - Use `firefly-workflow` agent for product photography pipeline
   - Generate background-removed product shots with custom backgrounds

3. **Marketing Campaign Assets**
   - Design campaign layouts with bencium skills
   - Generate on-brand imagery with Firefly style transfer
   - Create size variations for social, web, and print

---

## Environment Variables

```bash
# Adobe Firefly (required for image generation)
FIREFLY_CLIENT_ID=your_client_id
FIREFLY_CLIENT_SECRET=your_client_secret

# E2B Sandboxes (required for sandbox operations)
E2B_API_KEY=your_e2b_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Optional: GitHub integration
GITHUB_TOKEN=your_github_token
```

## Getting Started

### Firefly Setup

1. Get credentials at https://developer.adobe.com/console/
2. Install and register the MCP server:

```bash
cd apps/firefly_mcp
uv sync
uv run mcp install server.py --name "Adobe Firefly"
```

Or configure manually in `.mcp.json`:

```json
{
  "mcpServers": {
    "adobe-firefly": {
      "command": "uv",
      "args": ["run", "--directory", "apps/firefly_mcp", "python", "server.py"],
      "env": {
        "FIREFLY_CLIENT_ID": "your_client_id",
        "FIREFLY_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}
```

### Sandbox Setup

1. Get E2B API key at https://e2b.dev/docs
2. Copy environment: `cp .env.example .env`
3. Start with fundamentals: `cd apps/sandbox_fundamentals && uv sync`
4. Run examples: `uv run python 01_basic_sandbox.py`

## Firefly SDK CLI

The SDK includes a Typer CLI with mock testing support:

```bash
cd apps/firefly_sdk
uv sync

# Generate with mock mode (no credentials needed)
firefly generate "A sunset" --use-mocks --verbose

# Generate with all options
firefly generate "A cat coding" \
  --style photo \
  --aspect-ratio 16:9 \
  --seed 12345 \
  --download \
  --show-images

# Other commands
firefly expand <url> "prompt" --use-mocks
firefly remove-bg <url> --use-mocks
firefly similar <url> --use-mocks
firefly style <style-url> "prompt" --use-mocks
```

CLI Options: `--use-mocks`, `--download`, `--show-images`, `--verbose`, `--format json`

## Testing

```bash
# SDK tests (99 tests)
cd apps/firefly_sdk && uv run pytest --cov=firefly_sdk

# MCP tests (27 tests)
cd apps/firefly_mcp && uv run pytest --cov
```

## UV Python Examples

```bash
# Firefly examples
uv run apps/firefly_examples/01_generate_image.py "A sunset over mountains"
uv run apps/firefly_examples/02_remove_background.py https://example.com/image.jpg

# Sandbox fundamentals
cd apps/sandbox_fundamentals && uv run python 01_basic_sandbox.py
```

## Ralph Wiggum Integration

This project includes the ralph-wiggum plugin for iterative development:

```bash
/ralph-loop "Improve the plugin" --max-iterations 500 --completion-promise "TASK COMPLETE"
```
