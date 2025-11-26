# Adobe Firefly Claude Code Plugin

This repository provides a comprehensive Claude Code plugin for Adobe Firefly, enabling AI-powered image generation, manipulation, and creative workflows.

## Project Structure

```
claude-code-adobe-firefly/
├── .claude/                    # Claude Code configuration
│   ├── commands/               # Slash commands
│   │   ├── firefly-generate.md # Quick image generation
│   │   ├── firefly-edit.md     # Image editing operations
│   │   ├── firefly-workflow.md # Multi-step workflows
│   │   └── firefly-batch.md    # Batch processing
│   ├── agents/                 # Specialized agents
│   │   ├── firefly-creative.md # Creative generation agent
│   │   ├── firefly-editor.md   # Image editing agent
│   │   └── firefly-workflow.md # Workflow orchestration agent
│   ├── skills/                 # Reusable skills
│   │   ├── firefly-api.md      # API interaction skill
│   │   └── firefly-prompts.md  # Prompt engineering skill
│   └── settings.json           # Plugin and MCP server config
├── .claude-plugins/            # Installed plugins
│   └── ralph-wiggum/           # Iterative development plugin
├── src/                        # MCP server source (TypeScript)
│   ├── index.ts                # Main server entry
│   └── firefly-client.ts       # Adobe Firefly API client
├── apps/                       # Python applications
│   ├── firefly_sdk/            # UV Python SDK for Firefly
│   │   ├── src/firefly_sdk/    # SDK source code
│   │   │   ├── client.py       # API client
│   │   │   ├── models.py       # Pydantic models
│   │   │   ├── cli.py          # CLI interface
│   │   │   └── agent.py        # Claude Agent SDK integration
│   │   └── pyproject.toml      # UV project config
│   └── firefly_examples/       # Standalone UV scripts
│       ├── 01_generate_image.py
│       ├── 02_remove_background.py
│       ├── 03_expand_image.py
│       ├── 04_style_transfer.py
│       └── 05_claude_agent_workflow.py
├── agent-sandboxes/            # Reference implementation (cloned)
└── README.md                   # Project documentation
```

## Available MCP Tools

The Adobe Firefly MCP server exposes these tools:

1. **generate_image** - Generate images from text prompts
2. **expand_image** - Extend images beyond boundaries (generative expand)
3. **fill_image** - Replace portions using masks (generative fill)
4. **remove_background** - Automatic background removal
5. **generate_similar_images** - Create variations from reference
6. **apply_style_transfer** - Apply artistic styles

## Development Commands

- `/firefly-generate` - Quick image generation with customizable parameters
- `/firefly-edit` - Image editing (expand, fill, remove-bg, similar, style)
- `/firefly-workflow` - Multi-step creative workflows
- `/firefly-batch` - Batch image processing

## Agents

- `firefly-creative` - Creative image generation agent (Task tool, subagent_type: firefly-creative)
- `firefly-editor` - Image editing and manipulation agent
- `firefly-workflow` - Multi-step workflow orchestration agent

## Skills

- `firefly-api` - Core API interaction patterns and tool documentation
- `firefly-prompts` - Expert prompt engineering for image generation

## UV Python Examples

Run standalone scripts without installation:

```bash
# Generate an image
uv run apps/firefly_examples/01_generate_image.py "A sunset over mountains"

# Remove background
uv run apps/firefly_examples/02_remove_background.py https://example.com/image.jpg

# Multi-step workflow
uv run apps/firefly_examples/05_claude_agent_workflow.py product_photography
```

## Python SDK

Full async Python SDK with CLI:

```bash
cd apps/firefly_sdk
uv sync
firefly generate "Your prompt here"
```

## Environment Variables

Required:
- `FIREFLY_CLIENT_ID` - Adobe Developer Console client ID
- `FIREFLY_CLIENT_SECRET` - Adobe Developer Console client secret

## Getting Started

1. Set up Adobe Firefly API credentials at https://developer.adobe.com/console/
2. Install TypeScript dependencies: `npm install`
3. Build MCP server: `npm run build`
4. Configure Claude Code with the MCP server in `.claude/settings.json`
5. Use slash commands and agents in Claude Code

## Ralph Wiggum Integration

This project includes the ralph-wiggum plugin for iterative development:

```bash
# Start an iterative loop (max 500 iterations)
/ralph-loop "Improve the Firefly plugin" --max-iterations 500 --completion-promise "TASK COMPLETE"
```
