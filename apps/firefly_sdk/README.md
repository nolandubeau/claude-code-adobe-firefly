# Adobe Firefly SDK for Python

A comprehensive Python SDK for Adobe Firefly API, designed for use with Claude Code and Claude Agent SDK.

## Features

- Full Adobe Firefly API coverage
- Async/await support with httpx
- Pydantic models for type safety
- CLI for quick operations
- Claude Agent SDK integration
- UV-compatible for easy script execution

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

```bash
# Generate an image
firefly generate "A beautiful sunset over mountains" --width 1920 --height 1080

# Remove background
firefly remove-bg https://example.com/image.jpg

# Generate similar images
firefly similar https://example.com/reference.jpg --variations 4

# Apply style transfer
firefly style https://example.com/style.jpg "A modern city street" --strength 0.8
```

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

## License

MIT License
