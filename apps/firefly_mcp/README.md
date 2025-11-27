# Adobe Firefly MCP Server

Model Context Protocol (MCP) server that provides LLMs with access to Adobe Firefly's AI image generation capabilities through structured tool calls.

## Overview

This MCP server provides direct access to Adobe Firefly's APIs using Python/FastMCP, allowing LLMs to:

- Generate images from text prompts
- Expand images beyond their boundaries (generative expand)
- Fill/replace portions of images using masks (generative fill)
- Remove backgrounds from images
- Generate similar images from references
- Apply style transfer from reference images

## Architecture

```
┌─────────────────────────────────────────────────┐
│                                                 │
│  Claude / LLM Client                            │
│                                                 │
└───────────────────┬─────────────────────────────┘
                    │ MCP Protocol
                    │
┌───────────────────▼─────────────────────────────┐
│                                                 │
│  Adobe Firefly MCP Server (this app)            │
│  • 6 MCP Tools                                  │
│  • FastMCP Framework                            │
│  • Built-in Firefly client                      │
│                                                 │
└───────────────────┬─────────────────────────────┘
                    │ HTTPS/OAuth
                    │
┌───────────────────▼─────────────────────────────┐
│                                                 │
│  Adobe Firefly API                              │
│  • Image Generation v3                          │
│  • Image Expand v3                              │
│  • Image Fill v3                                │
│  • Background Removal v2                        │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Installation

```bash
# Navigate to this directory
cd apps/firefly_mcp

# Install dependencies
uv sync
```

## Configuration

Set these environment variables:

```bash
# Required - Adobe Developer Console credentials
export FIREFLY_CLIENT_ID="your_client_id"
export FIREFLY_CLIENT_SECRET="your_client_secret"
```

Or create a `.env` file in the project root.

### Getting Credentials

1. Go to [Adobe Developer Console](https://developer.adobe.com/console/)
2. Create a new project or select an existing one
3. Add the "Firefly - Firefly Services" API to your project
4. Generate OAuth Server-to-Server credentials
5. Copy your Client ID and Client Secret

## Quick Start

### Test with MCP Inspector

```bash
# Test the server interactively
uv run mcp dev server.py
```

This opens the MCP Inspector where you can:
- Browse available tools
- Test tool calls with different parameters
- See structured responses

### Install in Claude Desktop

```bash
# Install for use with Claude Desktop
uv run mcp install server.py

# Or with custom name
uv run mcp install server.py --name "Adobe Firefly"
```

### Configure in Claude Code

Add to your `.mcp.json` or `.claude/settings.json`:

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

## Available Tools

The server exposes 6 tools for image generation and manipulation:

### Image Generation

- **generate_image** - Generate images from text prompts with customizable dimensions, variations, and styles

### Image Editing

- **expand_image** - Extend images beyond their boundaries using AI
- **fill_image** - Replace portions of images using masks
- **remove_background** - Remove backgrounds, leaving only the main subject

### Image Variations

- **generate_similar_images** - Create variations based on a reference image
- **apply_style_transfer** - Apply the visual style of one image to new content

## Example Usage

Once installed, you can ask Claude:

```
"Generate an image of a sunset over mountains"
→ Calls generate_image(prompt="a sunset over mountains", width=1024, height=1024)

"Expand this image to make it wider"
→ Calls expand_image(image_url="...", prompt="continue the scene", target_width=2048)

"Remove the background from this product photo"
→ Calls remove_background(image_url="...")

"Generate 4 variations similar to this reference image"
→ Calls generate_similar_images(reference_image_url="...", num_variations=4)

"Apply the style of Van Gogh's Starry Night to a cityscape"
→ Calls apply_style_transfer(style_image_url="...", prompt="modern cityscape at night")
```

## Tool Parameters

### generate_image

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | str | required | Text description of the image |
| negative_prompt | str | None | What should NOT appear |
| width | int | 1024 | Image width (max 4096) |
| height | int | 1024 | Image height (max 4096) |
| num_variations | int | 1 | Number of images (1-4) |
| content_class | str | None | "photo" or "art" |
| style | str | None | Style preset name |
| seed | int | None | Seed for deterministic output |
| aspect_ratio | str | None | Aspect ratio (e.g., "16:9", "4:3") |
| output_format | str | None | Output format: "jpeg" or "png" |
| prompt_biasing_locale_code | str | None | Locale code (e.g., "en-US") |
| style_options | dict | None | Complex style object with presets |
| structure | dict | None | Structure reference object |

### expand_image

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | str | required | What to generate in expanded area |
| image_url | str | None | Source image URL |
| image_base64 | str | None | Base64 source image |
| target_width | int | None | Target width |
| target_height | int | None | Target height |
| horizontal_align | str | "center" | left/center/right |
| vertical_align | str | "center" | top/center/bottom |

### fill_image

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | str | required | What to generate in masked area |
| image_url | str | None | Source image URL |
| image_base64 | str | None | Base64 source image |
| mask_url | str | None | Mask image URL |
| mask_base64 | str | None | Base64 mask image |

### remove_background

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image_url | str | None | Image URL to process |
| image_base64 | str | None | Base64 image data |

### generate_similar_images

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| reference_image_url | str | None | Reference image URL |
| reference_image_base64 | str | None | Base64 reference |
| prompt | str | None | Guide the generation |
| num_variations | int | 1 | Number of images (1-4) |
| similarity | float | 0.5 | How similar (0.0-1.0) |

### apply_style_transfer

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | str | required | Content to generate |
| style_image_url | str | None | Style reference URL |
| style_image_base64 | str | None | Base64 style image |
| style_strength | float | 0.7 | Style intensity (0.0-1.0) |

## Implementation Details

### Authentication

- Uses OAuth 2.0 client credentials flow
- Tokens are cached and automatically refreshed
- 60-second buffer before expiry triggers refresh

### Error Handling

- Automatic retry with exponential backoff
- Retries on: rate limits, server errors, network issues
- Token refresh on 401 errors
- Content policy violations are not retried

### Response Format

All tools return structured dictionaries:

```python
# Image generation response
{
    "images": [
        {"url": "https://...", "seed": 12345},
        {"url": "https://...", "seed": 12346}
    ],
    "content_class": "photo"
}

# Background removal response
{
    "url": "https://..."
}
```

## Development

### Project Structure

```
apps/firefly_mcp/
├── server.py           # Main MCP server with Firefly client
├── pyproject.toml      # Project dependencies and metadata
└── README.md           # This file
```

### Running Locally

```bash
# Run with stdio transport (default)
uv run python server.py

# Or use mcp dev for interactive testing
uv run mcp dev server.py
```

### Adding New Tools

To add a new Firefly API endpoint:

1. Add the API method to the `FireflyClient` class
2. Create a new `@mcp.tool()` decorated async function
3. Call `client._request()` with the endpoint and body
4. Document parameters with docstrings

## API Documentation

- [Adobe Firefly Services Docs](https://developer.adobe.com/firefly-services/docs/)
- [Firefly API Reference](https://developer.adobe.com/firefly-services/docs/firefly-api/)
- [Image Generation API](https://developer.adobe.com/firefly-services/docs/firefly-api/guides/api/image_generation/)

## Use Cases

### Marketing Assets
```
"Generate a hero image for our SaaS landing page with abstract tech patterns"
```

### Product Photography
```
"Remove the background from this product photo and expand it to 16:9 aspect ratio"
```

### Creative Workflows
```
"Apply the style of this brand mood board to generate 4 variations of a banner image"
```

### Content Creation
```
"Generate a photorealistic image of a coffee shop interior with morning light"
```

## Testing

The MCP server includes comprehensive tests:

```bash
cd apps/firefly_mcp

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov --cov-report=term-missing

# Run with verbose output
uv run pytest -v
```

Tests cover:
- All 6 MCP tools
- Error handling and validation
- FireflyClient functionality
- Parameter validation

## License

MIT
