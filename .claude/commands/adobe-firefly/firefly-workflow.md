---
description: "Run a multi-step Adobe Firefly creative workflow"
argument-hint: "<workflow-type> [options]"
---

# Adobe Firefly Creative Workflow

Execute multi-step creative workflows combining multiple Firefly capabilities.

## Arguments

Parse from: $ARGUMENTS

Workflow types:
- `product-shot` - Generate product photography with background removal and placement
- `art-series` - Create a series of related artistic images
- `brand-assets` - Generate consistent brand imagery
- `concept-exploration` - Explore variations of a concept

## Workflow: Product Shot

1. Generate initial product image or use provided image
2. Remove background using `remove_background`
3. Generate new background using `generate_image`
4. Composite using `fill_image` with mask

## Workflow: Art Series

1. Generate initial image with style
2. Use `generate_similar_images` for variations
3. Apply consistent style transfer across series

## Workflow: Brand Assets

1. Define brand style parameters
2. Generate hero image
3. Create variations for different sizes/formats
4. Ensure consistency with style transfer

## Workflow: Concept Exploration

1. Generate initial concept
2. Create multiple variations with different parameters
3. Expand promising concepts
4. Iterate based on feedback

## Example Usage

```
/firefly-workflow product-shot --product "minimalist watch" --background "marble surface with soft lighting"
/firefly-workflow art-series --theme "seasons" --style "watercolor" --count 4
/firefly-workflow concept-exploration --idea "futuristic transportation" --variations 6
```

## Instructions

1. Parse the workflow type and options
2. Execute each step sequentially using appropriate MCP tools
3. Track intermediate results
4. Present final outputs with URLs and metadata
5. Offer to iterate or adjust based on results
