---
description: "Generate an image using Adobe Firefly AI"
argument-hint: "<prompt> [--style art|photo] [--size WxH]"
---

# Adobe Firefly Image Generation

Generate an image using Adobe Firefly based on the provided prompt.

## Arguments

Parse the arguments from: $ARGUMENTS

Expected format: `<prompt> [--style art|photo] [--size WxH] [--variations N]`

## Instructions

1. Parse the prompt and optional flags from the arguments
2. Use the `mcp__adobe-firefly__generate_image` tool with:
   - `prompt`: The text description
   - `contentClass`: "art" or "photo" (default: "photo")
   - `width` and `height`: From --size or default 1024x1024
   - `numVariations`: From --variations or default 1

3. Display the result including:
   - The generated image URL(s)
   - Any seeds for reproducibility
   - Cost/usage information if available

## Example Usage

```
/firefly-generate A serene mountain landscape at sunset --style photo --size 1920x1080
/firefly-generate Abstract geometric patterns in neon colors --style art --variations 4
```
