# claude-code-adobe-firefly

An MCP (Model Context Protocol) server that integrates Adobe Firefly's AI image generation capabilities with Claude Code.

## Features

- **Image Generation**: Generate images from text prompts with customizable dimensions and styles
- **Generative Expand**: Extend images beyond their original boundaries
- **Generative Fill**: Replace or fill portions of images using masks
- **Background Removal**: Remove backgrounds from images automatically
- **Similar Image Generation**: Create variations based on reference images
- **Style Transfer**: Apply artistic styles from reference images to new content

## Prerequisites

- Node.js 18+
- Adobe Developer Console account with Firefly API access
- Claude Code CLI

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/nolandubeau/claude-code-adobe-firefly.git
   cd claude-code-adobe-firefly
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Build the project:
   ```bash
   npm run build
   ```

4. Create a `.env` file with your Adobe credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

## Getting Adobe Firefly API Credentials

1. Go to [Adobe Developer Console](https://developer.adobe.com/console/)
2. Create a new project or select an existing one
3. Add the "Firefly - Firefly Services" API to your project
4. Generate OAuth Server-to-Server credentials
5. Copy your Client ID and Client Secret to your `.env` file

## Usage with Claude Code

Add this server to your Claude Code MCP configuration:

### Option 1: Global Configuration

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "adobe-firefly": {
      "command": "node",
      "args": ["/path/to/claude-code-adobe-firefly/dist/index.js"],
      "env": {
        "FIREFLY_CLIENT_ID": "your_client_id",
        "FIREFLY_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}
```

### Option 2: Project Configuration

Add to `.claude/settings.json` in your project:

```json
{
  "mcpServers": {
    "adobe-firefly": {
      "command": "node",
      "args": ["./node_modules/claude-code-adobe-firefly/dist/index.js"],
      "env": {
        "FIREFLY_CLIENT_ID": "your_client_id",
        "FIREFLY_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}
```

## Available Tools

### `generate_image`

Generate images from a text prompt.

**Parameters:**
- `prompt` (required): Text description of the image to generate
- `negativePrompt`: What should NOT appear in the image
- `width`: Image width in pixels (default: 1024)
- `height`: Image height in pixels (default: 1024)
- `numVariations`: Number of images to generate (1-4)
- `contentClass`: Either "photo" or "art"
- `style`: Style preset to apply

### `expand_image`

Expand an image beyond its current boundaries.

**Parameters:**
- `imageUrl` or `imageBase64`: Source image
- `prompt` (required): Description of the expanded content
- `targetWidth`: Target width in pixels
- `targetHeight`: Target height in pixels
- `placement`: Alignment of original image (`horizontalAlign`, `verticalAlign`)

### `fill_image`

Fill or replace portions of an image using a mask.

**Parameters:**
- `imageUrl` or `imageBase64`: Source image
- `maskUrl` or `maskBase64`: Mask image (white = fill, black = preserve)
- `prompt` (required): Description of the fill content

### `remove_background`

Remove the background from an image.

**Parameters:**
- `imageUrl` or `imageBase64`: Source image

### `generate_similar_images`

Generate images similar to a reference.

**Parameters:**
- `referenceImageUrl` or `referenceImageBase64`: Reference image
- `prompt`: Optional guiding prompt
- `numVariations`: Number of variations (1-4)
- `similarity`: Similarity to reference (0-1)

### `apply_style_transfer`

Apply a style from a reference image to new content.

**Parameters:**
- `styleImageUrl` or `styleImageBase64`: Style reference image
- `prompt` (required): Content to generate with the style
- `styleStrength`: Strength of style application (0-1)

## Development

```bash
# Run in development mode
npm run dev

# Type check
npm run typecheck

# Lint
npm run lint
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Resources

- [Adobe Firefly Services Documentation](https://developer.adobe.com/firefly-services/docs/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)
