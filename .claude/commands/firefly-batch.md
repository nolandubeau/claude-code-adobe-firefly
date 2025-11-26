---
description: "Batch process multiple images with Adobe Firefly"
argument-hint: "<action> <source> [options]"
---

# Adobe Firefly Batch Processing

Process multiple images in batch using Adobe Firefly.

## Arguments

Parse from: $ARGUMENTS

Format: `<action> <source> [options]`

Actions:
- `generate` - Generate multiple images from prompts file
- `remove-bg` - Remove backgrounds from multiple images
- `style` - Apply style to multiple images
- `resize` - Expand/resize multiple images

Source:
- File path containing URLs (one per line)
- Directory path with images
- Comma-separated URLs

## Instructions

1. Parse action and source
2. Load image list from source
3. Process each image with appropriate MCP tool
4. Track progress and results
5. Report summary with success/failure counts

## Example Usage

```
/firefly-batch remove-bg ./images/products/
/firefly-batch style ./images/photos.txt --style-image https://example.com/style.jpg
/firefly-batch generate ./prompts.txt --style art --output ./generated/
```

## Output

For each processed image:
- Original URL/path
- Result URL
- Status (success/error)
- Processing time

Summary:
- Total processed
- Successful
- Failed
- Total time
