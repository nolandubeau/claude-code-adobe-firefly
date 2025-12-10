# Adobe Firefly MCP Hub

A comprehensive Model Context Protocol (MCP) server providing unified access to Adobe Firefly Services APIs, modeled after the [Docker Hub MCP](https://github.com/docker/hub-mcp) architecture.

## Features

- **Firefly API** - Text-to-image, expand, fill, background removal, similar images, style transfer
- **Photoshop API** - Actions, renditions, text editing, smart objects, product crop
- **Lightroom API** - Auto-tone, auto-straighten, presets, XMP settings, adjustments
- **Content Tagging API** - Auto-tagging, color extraction
- **Video API** (Beta) - Text-to-video, image-to-video generation

## Installation

```bash
# Install dependencies
npm install

# Build
npm run build

# Run
npm start
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FIREFLY_CLIENT_ID` | Yes | Adobe Developer Console client ID |
| `FIREFLY_CLIENT_SECRET` | Yes | Adobe Developer Console client secret |
| `MCP_TRANSPORT` | No | Transport type: `stdio` (default) or `http` |
| `MCP_HTTP_PORT` | No | HTTP port (default: 3000) |
| `MCP_LOG_LEVEL` | No | Log level: `error`, `warn`, `info`, `debug` |
| `MCP_LOGS_DIR` | No | Log directory |

### Getting Credentials

1. Go to [Adobe Developer Console](https://developer.adobe.com/console/)
2. Create a new project
3. Add the Firefly Services API
4. Generate credentials (OAuth Server-to-Server)

## Usage

### With MCP Clients (Claude Desktop, etc.)

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "adobe-firefly-hub": {
      "command": "node",
      "args": ["/path/to/firefly-mcp-hub/dist/index.js"],
      "env": {
        "FIREFLY_CLIENT_ID": "your_client_id",
        "FIREFLY_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}
```

### CLI Options

```bash
# Start with STDIO transport (default)
node dist/index.js

# Start with HTTP transport
node dist/index.js --transport http --port 8080

# Disable specific modules
node dist/index.js --disable-photoshop --disable-video

# Show help
node dist/index.js --help
```

### Docker

```bash
# Build
docker build -t firefly-mcp-hub .

# Run with STDIO
docker run -it \
  -e FIREFLY_CLIENT_ID=xxx \
  -e FIREFLY_CLIENT_SECRET=yyy \
  firefly-mcp-hub

# Run with HTTP
docker run -d \
  -e FIREFLY_CLIENT_ID=xxx \
  -e FIREFLY_CLIENT_SECRET=yyy \
  -e MCP_TRANSPORT=http \
  -p 3000:3000 \
  firefly-mcp-hub
```

## Available Tools

### Firefly (Image Generation)

| Tool | Description |
|------|-------------|
| `firefly_generate_image` | Generate images from text prompts |
| `firefly_expand_image` | Expand images beyond boundaries (outpainting) |
| `firefly_fill_image` | Fill masked areas (inpainting) |
| `firefly_remove_background` | Remove background from images |
| `firefly_generate_similar` | Generate similar images |
| `firefly_style_transfer` | Apply style from reference image |

### Photoshop (Image Processing)

| Tool | Description |
|------|-------------|
| `photoshop_apply_actions` | Apply Photoshop actions |
| `photoshop_create_rendition` | Generate image renditions |
| `photoshop_edit_text` | Edit text layers |
| `photoshop_smart_object` | Replace smart object contents |
| `photoshop_remove_background` | AI background removal |
| `photoshop_product_crop` | Smart product cropping |
| `photoshop_get_manifest` | Extract PSD document manifest |
| `photoshop_job_status` | Check async job status |

### Lightroom (Image Enhancement)

| Tool | Description |
|------|-------------|
| `lightroom_auto_tone` | Apply automatic tone adjustment |
| `lightroom_auto_straighten` | Correct horizon automatically |
| `lightroom_apply_preset` | Apply Lightroom presets |
| `lightroom_apply_xmp` | Apply XMP sidecar settings |
| `lightroom_edit` | Apply custom adjustments |
| `lightroom_job_status` | Check async job status |

### Content Tagging

| Tool | Description |
|------|-------------|
| `content_auto_tag` | Generate content tags/keywords |
| `content_extract_colors` | Extract dominant colors |

### Video (Beta)

| Tool | Description |
|------|-------------|
| `video_text_to_video` | Generate video from text |
| `video_image_to_video` | Animate image to video |
| `video_get_status` | Check video job status |

## Architecture

```
src/
├── index.ts          # CLI entry point
├── server.ts         # MCP server implementation
├── asset.ts          # Base asset class (auth, retry, logging)
├── types.ts          # Shared Zod schemas
├── logger.ts         # Winston logging
├── firefly/          # Firefly API module
├── photoshop/        # Photoshop API module
├── lightroom/        # Lightroom API module
├── content/          # Content Tagging module
└── video/            # Video API module (beta)
```

## Development

```bash
# Install dependencies
npm install

# Run in development mode
npm run dev

# Type checking
npm run typecheck

# Lint
npm run lint

# Format
npm run format

# Test
npm test
```

## Testing with MCP Inspector

```bash
npm run inspector
```

## API Documentation

- [Firefly API](https://developer.adobe.com/firefly-services/docs/firefly-api/)
- [Photoshop API](https://developer.adobe.com/firefly-services/docs/photoshop/)
- [Lightroom API](https://developer.adobe.com/firefly-services/docs/lightroom/)
- [Firefly Services Guide](https://developer.adobe.com/firefly-services/docs/guides/)

## License

Apache-2.0
