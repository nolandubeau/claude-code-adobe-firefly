# Adobe Firefly Examples

Standalone UV Python scripts demonstrating Adobe Firefly API capabilities.

## Prerequisites

1. Set environment variables:
   ```bash
   export FIREFLY_CLIENT_ID="your_client_id"
   export FIREFLY_CLIENT_SECRET="your_client_secret"
   ```

2. Install UV: https://docs.astral.sh/uv/

## Examples

### 01 - Basic Image Generation

Generate images from text prompts.

```bash
uv run apps/firefly_examples/01_generate_image.py "A serene mountain landscape at sunset"
```

### 02 - Background Removal

Remove backgrounds from images.

```bash
uv run apps/firefly_examples/02_remove_background.py https://example.com/photo.jpg
```

### 03 - Image Expansion (Outpainting)

Extend images beyond their boundaries.

```bash
uv run apps/firefly_examples/03_expand_image.py https://example.com/photo.jpg "continue the forest scene"
```

### 04 - Style Transfer

Apply artistic styles to new content.

```bash
uv run apps/firefly_examples/04_style_transfer.py https://example.com/vangogh.jpg "a modern cityscape" 0.8
```

### 05 - Claude Agent Workflow

Multi-step creative workflows designed for Claude Agent SDK integration.

```bash
# Product photography workflow
uv run apps/firefly_examples/05_claude_agent_workflow.py product_photography

# Art series workflow
uv run apps/firefly_examples/05_claude_agent_workflow.py art_series

# Concept exploration workflow
uv run apps/firefly_examples/05_claude_agent_workflow.py concept_exploration
```

## UV Script Format

All examples use the PEP 723 inline script metadata format:

```python
#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "httpx>=0.27.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
```

This allows running scripts without installing a package - UV handles dependencies automatically.

## Integration with Claude Code

These examples complement the Claude Code plugin by providing:

1. **Standalone scripts** for quick testing
2. **Workflow patterns** for multi-step operations
3. **Claude Agent SDK integration** patterns

The same patterns can be used in:
- Custom Claude Code commands
- Claude Agent SDK tools
- Automated pipelines
