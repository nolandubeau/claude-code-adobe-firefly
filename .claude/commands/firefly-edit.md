---
description: "Edit an image using Adobe Firefly (expand, fill, remove background)"
argument-hint: "<action> <image-url> [options]"
---

# Adobe Firefly Image Editing

Edit images using Adobe Firefly's generative capabilities.

## Arguments

Parse from: $ARGUMENTS

Expected format: `<action> <image-url> [options]`

Actions:
- `expand` - Extend image beyond boundaries
- `fill` - Replace masked areas
- `remove-bg` - Remove background
- `similar` - Generate similar images
- `style` - Apply style transfer

## Instructions

Based on the action, use the appropriate MCP tool:

### Expand Action
Use `mcp__adobe-firefly__expand_image`:
- `imageUrl`: The source image URL
- `prompt`: Description of expanded content (required)
- `targetWidth`, `targetHeight`: New dimensions
- `placement`: Alignment options

### Fill Action
Use `mcp__adobe-firefly__fill_image`:
- `imageUrl`: Source image
- `maskUrl`: Mask image (white = fill areas)
- `prompt`: Description of fill content

### Remove Background Action
Use `mcp__adobe-firefly__remove_background`:
- `imageUrl`: Source image

### Similar Action
Use `mcp__adobe-firefly__generate_similar_images`:
- `referenceImageUrl`: Reference image
- `prompt`: Optional guiding prompt
- `similarity`: 0-1 (default 0.5)
- `numVariations`: 1-4

### Style Transfer Action
Use `mcp__adobe-firefly__apply_style_transfer`:
- `styleImageUrl`: Style reference
- `prompt`: Content description
- `styleStrength`: 0-1 (default 0.7)

## Example Usage

```
/firefly-edit expand https://example.com/image.jpg --prompt "continue the forest scene" --size 2048x1024
/firefly-edit remove-bg https://example.com/portrait.jpg
/firefly-edit style https://example.com/vangogh.jpg --prompt "a modern city street" --strength 0.8
```
