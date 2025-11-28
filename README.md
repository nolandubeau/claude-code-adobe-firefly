# Claude Code Adobe Firefly + Agent Sandboxes

A comprehensive Claude Code plugin combining Adobe Firefly's AI image generation with E2B Agent Sandboxes for scalable agentic engineering.

## Overview

This repository provides two powerful capabilities:

1. **Adobe Firefly MCP Server** - AI-powered image generation, manipulation, and creative workflows
2. **Agent Sandboxes (E2B)** - Isolated, scalable sandbox environments for parallel agent experiments

![Agent Sandboxes Architecture](images/agent_sandboxes_snapshot.png)

---

## Adobe Firefly MCP Server

An MCP (Model Context Protocol) server that integrates Adobe Firefly's AI image generation capabilities with Claude Code.

### Features

- **Image Generation**: Generate images from text prompts with customizable dimensions and styles
- **Generative Expand**: Extend images beyond their original boundaries
- **Generative Fill**: Replace or fill portions of images using masks
- **Background Removal**: Remove backgrounds from images automatically
- **Similar Image Generation**: Create variations based on reference images
- **Style Transfer**: Apply artistic styles from reference images to new content

### Prerequisites

- Python 3.11+ with [UV](https://docs.astral.sh/uv/)
- Adobe Developer Console account with Firefly API access
- Claude Code CLI

### Installation

```bash
# Clone the repository
git clone https://github.com/nolandubeau/claude-code-adobe-firefly.git
cd claude-code-adobe-firefly

# Install and register the MCP server
cd apps/firefly_mcp
uv sync
uv run mcp install server.py --name "Adobe Firefly"
```

Set environment variables:

```bash
export FIREFLY_CLIENT_ID="your_client_id"
export FIREFLY_CLIENT_SECRET="your_client_secret"
```

### Getting Adobe Firefly API Credentials

1. Go to [Adobe Developer Console](https://developer.adobe.com/console/)
2. Create a new project or select an existing one
3. Add the "Firefly - Firefly Services" API to your project
4. Generate OAuth Server-to-Server credentials
5. Copy your Client ID and Client Secret to your `.env` file

### Usage with Claude Code

The easiest way to register the MCP server:

```bash
cd apps/firefly_mcp
uv run mcp install server.py --name "Adobe Firefly"
```

Or manually add to `~/.claude/settings.json` or `.mcp.json`:

```json
{
  "mcpServers": {
    "adobe-firefly": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/apps/firefly_mcp", "python", "server.py"],
      "env": {
        "FIREFLY_CLIENT_ID": "your_client_id",
        "FIREFLY_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}
```

### Available Tools

| Tool | Description |
|------|-------------|
| `generate_image` | Generate images from text prompts |
| `expand_image` | Extend images beyond boundaries |
| `fill_image` | Replace portions using masks |
| `remove_background` | Remove image backgrounds |
| `generate_similar_images` | Create variations from reference |
| `apply_style_transfer` | Apply artistic styles |

See [CLAUDE.md](CLAUDE.md) for detailed tool parameters and usage.

---

## Agent Sandboxes (E2B)

Using Agent Sandboxes for complete agentic engineering control with isolation, scale, and full agency.

> Watch the full video breakdown: [Agent Sandboxes + Claude Code](https://youtu.be/1ECn5zrVUB4)

### Value Proposition

Agent Sandboxes unlock 3 key capabilities:

- **Isolation**: Each agent fork runs in a fully isolated, gated E2B sandbox - safe from your local filesystem and production environment
- **Scale**: Run as many agent forks as you want, each independent with its own sandbox
- **Agency**: Agents have full control - install packages, modify files, run commands, handle more of the engineering process

### Apps

#### Adobe Firefly

| App | Description |
|-----|-------------|
| `firefly_mcp/` | **MCP server** for Firefly (Python/FastMCP) - recommended |
| `firefly_sdk/` | Python SDK with **Typer CLI** and mock testing |
| `firefly_examples/` | Standalone example scripts |

**SDK Features:**
- Typer CLI with `--use-mocks`, `--download`, `--show-images`, `--verbose`
- Full API coverage: seed, aspect_ratio, style_options, structure
- 126 tests with comprehensive coverage

#### E2B Sandboxes

| App | Description |
|-----|-------------|
| `sandbox_workflows/` | **obox**: Run parallel agent forks in isolated E2B sandboxes |
| `sandbox_mcp/` | MCP server wrapping sandbox_cli for LLM integration |
| `sandbox_cli/` | Click CLI for E2B sandbox management |
| `sandbox_fundamentals/` | E2B SDK learning examples and patterns |
| `cc_in_sandbox/` | Run Claude Code agent inside an E2B sandbox (ibox) |
| `sandbox_agent_working_dir/` | Agent runtime working directory |

### Quick Start - Sandboxes

#### 1. Environment Setup

Create a `.env` file in the project root:

```bash
# Adobe Firefly (required for image generation)
FIREFLY_CLIENT_ID=your_firefly_client_id_here
FIREFLY_CLIENT_SECRET=your_firefly_client_secret_here

# E2B Sandboxes (required for sandbox operations)
E2B_API_KEY=your_e2b_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional: Required for git push/PR functionality
GITHUB_TOKEN=your_github_token_here
```

**Get your API keys:**

- **Firefly Credentials**: [Adobe Developer Console](https://developer.adobe.com/console/) - Create a project with Firefly Services API
- **E2B API Key**: [https://e2b.dev/docs](https://e2b.dev/docs)
- **Anthropic API Key**: [https://console.anthropic.com/](https://console.anthropic.com/)
- **GitHub Token**: [GitHub PAT docs](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) - Create with `repo` scope

#### 2. Learning Path

Work from fundamentals to full workflows:

1. **E2B Fundamentals** - `apps/sandbox_fundamentals/`
2. **CLI Tools** - `apps/sandbox_cli/`
3. **MCP Server** - `apps/sandbox_mcp/`
4. **Workflows** - `apps/sandbox_workflows/`

#### 3. Explore E2B Fundamentals

```bash
cd apps/sandbox_fundamentals
uv sync

# Run examples in order
uv run python 01_basic_sandbox.py
uv run python 02_list_files.py
uv run python 03_file_operations.py
# ... through 13_expose_vite_vue_webserver.py
```

#### 4. Use CLI for Sandbox Management

```bash
cd apps/sandbox_cli
uv sync

uv run python src/main.py --help
uv run python src/main.py init
uv run python src/main.py sandbox create --template agent-sandbox-dev-node22
uv run python src/main.py exec <sandbox-id> "ls -la"
```

#### 5. Use MCP Server with Claude

```bash
# Copy sandbox MCP config
cp .mcp.json.sandbox .mcp.json
# Edit with your E2B API key

# Start Claude Code
claude

# Check MCP status
/mcp

# Use natural language
prompt: init a new sandbox
prompt: run ls -la in the sandbox
```

#### 6. Run Parallel Agent Experiments (obox)

```bash
cp .mcp.json apps/sandbox_agent_working_dir/.mcp.json
cp .env apps/sandbox_agent_working_dir/.env

cd apps/sandbox_workflows
uv sync
uv run obox <repo-url> --branch <branch> --model <opus|sonnet|haiku> --prompt "your task" --forks 3
```

---

## Development

```bash
# Test Firefly MCP with MCP Inspector
cd apps/firefly_mcp
uv run mcp dev server.py

# Run Firefly MCP directly
uv run python server.py

# Run Firefly SDK CLI (with mocks for testing)
cd apps/firefly_sdk
uv sync
firefly generate "A sunset" --use-mocks --verbose

# Run Firefly SDK examples
cd apps/firefly_examples
uv run python 01_generate_image.py "A sunset over mountains"
```

### Testing

```bash
# Run SDK tests (99 tests)
cd apps/firefly_sdk
uv run pytest --cov=firefly_sdk

# Run MCP tests (27 tests)
cd apps/firefly_mcp
uv run pytest --cov

# Total: 126 tests
```

---

## Bencium UX Designer Skills

This plugin includes two specialized UX design skills for creating distinctive, production-grade interfaces:

### Available Skills

| Skill | Description |
|-------|-------------|
| `bencium-controlled-ux-designer` | Systematic, production-focused design with careful decision-making. Always asks before making design decisions. Best for accessible, consistent interfaces. |
| `bencium-innovative-ux-designer` | Bold, creative design that avoids generic AI aesthetics. Commits to distinctive visual directions. Best for memorable, visually striking interfaces. |

### Using the Skills

Invoke skills via Claude Code:

```
Use the bencium-controlled-ux-designer skill to help me design this form
```

```
Use the bencium-innovative-ux-designer skill for this landing page
```

### Key Differences

**Controlled UX Designer:**
- Always asks before making design decisions
- Prefers flat, minimal design without shadows
- Systematic approach to colors, typography, layouts
- Best for: Production apps, dashboards, forms

**Innovative UX Designer:**
- Commits boldly to distinctive aesthetic directions
- Uses shadows, gradients, textures when intentional
- Breaks from generic SaaS patterns
- Best for: Landing pages, marketing sites, portfolios

---

## Integration Examples

The `docs/examples/` directory contains detailed integration patterns combining Firefly image generation with Bencium UX design skills:

### Basic Integrations

| Example | Description |
|---------|-------------|
| [01-saas-landing-page.md](docs/examples/01-saas-landing-page.md) | SaaS landing page with AI-generated hero imagery |
| [02-product-showcase.md](docs/examples/02-product-showcase.md) | E-commerce with product photography pipeline |
| [03-creative-portfolio.md](docs/examples/03-creative-portfolio.md) | Agency portfolio with layered visuals |
| [04-dashboard-app.md](docs/examples/04-dashboard-app.md) | Dashboard with custom AI illustrations |

### Scaled Workflows (E2B Sandboxes + Firefly + Bencium)

| Example | Description | Scale |
|---------|-------------|-------|
| [05-parallel-design-exploration.md](docs/examples/05-parallel-design-exploration.md) | Explore multiple design directions simultaneously | 4+ forks |
| [06-ab-landing-page-scale.md](docs/examples/06-ab-landing-page-scale.md) | Generate A/B test variants in parallel | 8 forks |
| [07-brand-identity-exploration.md](docs/examples/07-brand-identity-exploration.md) | Create complete brand systems simultaneously | 5 forks |
| [08-product-photography-pipeline.md](docs/examples/08-product-photography-pipeline.md) | Process product catalogs with background generation | 10+ forks |

### Example Workflows

**1. App Design with Generated Hero Images**
- Use `bencium-innovative-ux-designer` to design the page layout
- Use `/firefly-generate` to create hero imagery matching the design aesthetic
- Integrate generated images into the final design

**2. Product Landing Page**
- Use `bencium-controlled-ux-designer` for accessible, production-ready layouts
- Use `firefly-workflow` agent for product photography pipeline
- Generate background-removed product shots with custom backgrounds

**3. Marketing Campaign Assets**
- Design campaign layouts with bencium skills
- Generate on-brand imagery with Firefly style transfer
- Create size variations for social, web, and print

**4. Parallel Design Brainstorming (NEW)**
- Launch 4-10 sandbox forks with different design directions
- Each fork uses Bencium skills + Firefly for complete designs
- Compare all results side-by-side in hours instead of weeks

---

## Resources

### Adobe Firefly

- [Adobe Firefly Services Documentation](https://developer.adobe.com/firefly-services/docs/)
- [Adobe Developer Console](https://developer.adobe.com/console/)

### Claude Code

- [Claude Code Product Page](https://www.claude.com/product/claude-code)
- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)
- [Model Context Protocol](https://modelcontextprotocol.io/)

### E2B Sandboxes

- [E2B Documentation](https://e2b.dev/)
- [Claude Agent SDK](https://docs.claude.com/en/docs/agent-sdk/python)

---

## License

MIT License - see [LICENSE](LICENSE) for details.
