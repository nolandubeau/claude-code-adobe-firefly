---
name: firefly-api
description: "Core Adobe Firefly API interaction skill. Use when working with Adobe Firefly for image generation, editing, and manipulation tasks."
---

# Adobe Firefly API Skill

This skill provides knowledge and patterns for interacting with Adobe Firefly APIs through the MCP server.

## Available Tools

### generate_image
Generate images from text prompts.

**Parameters:**
- `prompt` (required): Text description of the image
- `negativePrompt`: What to avoid in the image
- `width`: Image width (default: 1024)
- `height`: Image height (default: 1024)
- `numVariations`: Number of images to generate (1-4)
- `contentClass`: "photo" or "art"
- `style`: Style preset name

**Example:**
```json
{
  "prompt": "A majestic mountain landscape at golden hour with dramatic clouds",
  "contentClass": "photo",
  "width": 1920,
  "height": 1080,
  "numVariations": 2
}
```

### expand_image
Extend an image beyond its boundaries.

**Parameters:**
- `imageUrl` or `imageBase64`: Source image
- `prompt` (required): Description of expanded content
- `targetWidth`: New width
- `targetHeight`: New height
- `placement`: Alignment of original image

**Example:**
```json
{
  "imageUrl": "https://example.com/image.jpg",
  "prompt": "Continue the forest scene with more trees and a river",
  "targetWidth": 2048,
  "targetHeight": 1024,
  "placement": {
    "horizontalAlign": "center",
    "verticalAlign": "center"
  }
}
```

### fill_image
Replace portions of an image using a mask.

**Parameters:**
- `imageUrl` or `imageBase64`: Source image
- `maskUrl` or `maskBase64`: Mask (white = fill areas)
- `prompt` (required): Description of fill content

**Example:**
```json
{
  "imageUrl": "https://example.com/scene.jpg",
  "maskUrl": "https://example.com/mask.png",
  "prompt": "A modern sports car"
}
```

### remove_background
Remove the background from an image.

**Parameters:**
- `imageUrl` or `imageBase64`: Source image

**Returns:** Image with transparent background

### generate_similar_images
Create variations based on a reference image.

**Parameters:**
- `referenceImageUrl` or `referenceImageBase64`: Reference image
- `prompt`: Optional guiding prompt
- `numVariations`: Number of variations (1-4)
- `similarity`: How similar to reference (0-1)

### apply_style_transfer
Apply the style of one image to new content.

**Parameters:**
- `styleImageUrl` or `styleImageBase64`: Style reference
- `prompt` (required): Content to generate
- `styleStrength`: Style intensity (0-1)

## Best Practices

### Prompt Writing
1. Be specific about subject, composition, lighting
2. Include artistic style references when relevant
3. Use negative prompts to exclude unwanted elements
4. Describe mood and atmosphere

### Parameter Selection
- **Photo-realistic**: `contentClass: "photo"`, detailed prompts
- **Artistic**: `contentClass: "art"`, style references
- **Variations**: Start with more, refine from best
- **Expansion**: Match prompt to existing image style

### Error Handling
- Check for valid URLs before API calls
- Handle rate limits with retries
- Validate image dimensions within limits
- Cache results for reproducibility

## Authentication

The MCP server handles OAuth authentication automatically using:
- `FIREFLY_CLIENT_ID`: Adobe Developer Console client ID
- `FIREFLY_CLIENT_SECRET`: Adobe Developer Console client secret

Tokens are cached and refreshed automatically.
