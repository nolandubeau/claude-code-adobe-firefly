# Adobe Firefly SDK for Python

A comprehensive Python SDK for Adobe Firefly API, designed for use with Claude Code and Claude Agent SDK.

## Features

- Full Adobe Firefly API coverage with all parameters (seed, aspect_ratio, style, structure, etc.)
- Async/await support with httpx
- Pydantic models for type safety
- **Typer CLI** with rich output formatting
- **Mock mode** for testing without API credentials (`--use-mocks`)
- **Image download** and terminal display (`--download`, `--show-images`)
- Claude Agent SDK integration
- UV-compatible for easy script execution
- **126 tests** with comprehensive coverage

## Installation

### Using UV (Recommended)

```bash
cd apps/firefly_sdk
uv sync
```

### Using pip

```bash
pip install -e apps/firefly_sdk
```

## Configuration

Set environment variables:

```bash
export FIREFLY_CLIENT_ID="your_client_id"
export FIREFLY_CLIENT_SECRET="your_client_secret"
```

Or create a `.env` file:

```
FIREFLY_CLIENT_ID=your_client_id
FIREFLY_CLIENT_SECRET=your_client_secret
```

## Usage

### Python API

```python
import asyncio
from firefly_sdk import FireflyClient, GenerateImageRequest

async def main():
    async with FireflyClient() as client:
        # Generate an image
        request = GenerateImageRequest(
            prompt="A serene mountain landscape at sunset",
            width=1920,
            height=1080,
            content_class="photo",
        )
        response = await client.generate_image(request)

        for image in response.images:
            print(f"Generated: {image.url}")

asyncio.run(main())
```

### CLI

The CLI uses [Typer](https://typer.tiangolo.com/) for a rich command-line experience.

```bash
# Generate an image
firefly generate "A beautiful sunset over mountains" --width 1920 --height 1080

# Generate with all options
firefly generate "A cat coding" \
  --style photo \
  --aspect-ratio 16:9 \
  --seed 12345 \
  --variations 2 \
  --negative "no text, no watermark" \
  --download \
  --show-images \
  --verbose

# Test without API credentials (mock mode)
firefly generate "Test prompt" --use-mocks

# Remove background
firefly remove-bg https://example.com/image.jpg

# Expand an image
firefly expand https://example.com/image.jpg "extend the sky" --width 2048 --height 1024

# Generate similar images
firefly similar https://example.com/reference.jpg --variations 4 --similarity 0.8

# Apply style transfer
firefly style https://example.com/style.jpg "A modern city street" --strength 0.8

# Get JSON output
firefly generate "A sunset" --use-mocks --format json
```

### CLI Options

| Option | Description |
|--------|-------------|
| `--use-mocks` | Use mock API responses (no credentials needed) |
| `--download` | Download generated images to current directory |
| `--show-images` | Display images in terminal (requires imgcat) |
| `--verbose` | Show detailed operation information |
| `--format` | Output format: `text` (default) or `json` |
| `--style` | Content class: `photo` or `art` |
| `--aspect-ratio` | Aspect ratio: `1:1`, `16:9`, `4:3`, etc. |
| `--seed` | Seed for deterministic output |
| `--variations` | Number of images to generate (1-4) |
| `--negative` | Negative prompt (what to avoid) |

### UV Script Execution

```bash
# Run standalone scripts with UV
uv run apps/firefly_sdk/examples/generate_image.py "Your prompt here"
```

## Claude Agent SDK Integration

```python
from firefly_sdk.agent import FireflyAgentTools

async def setup_agent():
    # Get tool definitions for Claude Agent
    tool_definitions = FireflyAgentTools.TOOL_DEFINITIONS

    # Create tools instance
    async with FireflyAgentTools() as tools:
        # Execute a tool
        result = await tools.execute_tool(
            "firefly_generate_image",
            {"prompt": "A cute robot", "content_class": "art"}
        )
        print(result.data)
```

## API Reference

### FireflyClient Methods

- `generate_image(request)` - Generate images from text prompts
- `expand_image(request)` - Expand images beyond boundaries
- `fill_image(request)` - Fill portions using masks
- `remove_background(request)` - Remove image backgrounds
- `generate_similar(request)` - Generate similar images
- `apply_style_transfer(request)` - Apply style from reference

### Request Models

- `GenerateImageRequest` - Image generation parameters
- `ExpandImageRequest` - Image expansion parameters
- `FillImageRequest` - Generative fill parameters
- `RemoveBackgroundRequest` - Background removal parameters
- `GenerateSimilarRequest` - Similar image parameters
- `StyleTransferRequest` - Style transfer parameters

## Testing

The SDK includes comprehensive tests with mock infrastructure:

```bash
cd apps/firefly_sdk

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=firefly_sdk --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_cli.py -v
```

### Mock Mode

The `--use-mocks` flag enables testing without API credentials:

```bash
# Test CLI commands without real API calls
firefly generate "test" --use-mocks
firefly expand https://example.com/img.jpg "prompt" --use-mocks
firefly remove-bg https://example.com/img.jpg --use-mocks
firefly similar https://example.com/img.jpg --use-mocks
firefly style https://example.com/style.jpg "prompt" --use-mocks
```

## License

MIT License
