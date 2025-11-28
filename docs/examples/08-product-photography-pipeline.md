# Product Photography Pipeline at Scale

Process entire e-commerce product catalogs in parallel using sandbox forks, with Firefly for background generation and image manipulation.

## Scenario

An e-commerce company needs to:
- Process 500 product images
- Remove backgrounds
- Generate 5 lifestyle background variations per product
- Create size variants for web, mobile, social
- Generate seasonal campaign versions

**Traditional approach:** Weeks of manual work
**Parallel sandboxes:** Hours of automated processing

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  Product Catalog: 500 SKUs                                          │
│  Input: Raw product photos on white/gray backgrounds                │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │   Batch Distributor   │
                    │   50 products/fork    │
                    └───────────┬───────────┘
                                │
    ┌─────────┬─────────┬───────┼───────┬─────────┬─────────┐
    │         │         │       │       │         │         │
    ▼         ▼         ▼       ▼       ▼         ▼         ▼
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ... ┌───────┐
│Fork 1 │ │Fork 2 │ │Fork 3 │ │Fork 4 │ │Fork 5 │     │Fork 10│
│SKU    │ │SKU    │ │SKU    │ │SKU    │ │SKU    │     │SKU    │
│1-50   │ │51-100 │ │101-150│ │151-200│ │201-250│     │451-500│
└───────┘ └───────┘ └───────┘ └───────┘ └───────┘     └───────┘
    │         │         │       │       │         │
    └─────────┴─────────┴───────┼───────┴─────────┘
                                │
                    ┌───────────▼───────────┐
                    │   Aggregator & CDN    │
                    │   Upload Pipeline     │
                    └───────────────────────┘
```

## Product Processing Pipeline

### Step 1: Define Processing Config

```python
# product_pipeline_config.py

BACKGROUND_STYLES = [
    {
        "name": "studio-white",
        "prompt": "clean white studio background, soft shadows, professional product photography lighting",
        "use_case": "main_listing"
    },
    {
        "name": "lifestyle-home",
        "prompt": "modern minimalist home interior, natural daylight, lifestyle product placement",
        "use_case": "lifestyle"
    },
    {
        "name": "lifestyle-office",
        "prompt": "contemporary office desk setup, professional environment, soft ambient lighting",
        "use_case": "lifestyle"
    },
    {
        "name": "seasonal-summer",
        "prompt": "bright summer outdoor scene, natural sunlight, fresh and vibrant colors",
        "use_case": "campaign"
    },
    {
        "name": "seasonal-holiday",
        "prompt": "cozy holiday setting, warm lighting, festive decorations subtle in background",
        "use_case": "campaign"
    }
]

OUTPUT_SIZES = [
    {"name": "hero", "width": 1200, "height": 1200, "use": "product_page"},
    {"name": "thumbnail", "width": 400, "height": 400, "use": "category_grid"},
    {"name": "cart", "width": 200, "height": 200, "use": "shopping_cart"},
    {"name": "social-square", "width": 1080, "height": 1080, "use": "instagram"},
    {"name": "social-story", "width": 1080, "height": 1920, "use": "instagram_story"},
    {"name": "banner", "width": 1920, "height": 600, "use": "homepage_banner"}
]

PRODUCT_CATEGORIES = {
    "electronics": {
        "bg_preference": ["studio-white", "lifestyle-office"],
        "expand_ratio": 1.2,  # Add 20% padding
        "shadow_style": "soft-drop"
    },
    "fashion": {
        "bg_preference": ["lifestyle-home", "seasonal-*"],
        "expand_ratio": 1.3,
        "shadow_style": "natural"
    },
    "home-goods": {
        "bg_preference": ["lifestyle-home", "studio-white"],
        "expand_ratio": 1.4,
        "shadow_style": "ambient"
    },
    "outdoor": {
        "bg_preference": ["seasonal-summer", "lifestyle-*"],
        "expand_ratio": 1.5,
        "shadow_style": "natural-outdoor"
    }
}
```

### Step 2: Batch Distribution Script

```bash
#!/bin/bash
# distribute_products.sh

CATALOG_FILE="products.json"
PRODUCTS_PER_FORK=50
TOTAL_PRODUCTS=$(jq length $CATALOG_FILE)
NUM_FORKS=$((($TOTAL_PRODUCTS + $PRODUCTS_PER_FORK - 1) / $PRODUCTS_PER_FORK))

echo "Processing $TOTAL_PRODUCTS products across $NUM_FORKS sandbox forks"

cd apps/sandbox_workflows

for i in $(seq 0 $(($NUM_FORKS - 1))); do
    START=$(($i * $PRODUCTS_PER_FORK))
    END=$(($START + $PRODUCTS_PER_FORK))

    # Extract batch of products
    BATCH=$(jq ".[$START:$END]" $CATALOG_FILE)

    uv run obox https://github.com/your-org/product-processor.git \
        --branch "batch-${i}" \
        --model sonnet \
        --prompt "$(cat <<EOF
Process product batch ${i} (SKUs ${START}-${END})

Products to process:
${BATCH}

For EACH product in this batch:

## Step 1: Background Removal
- Use Firefly remove_background on the source image
- Save cutout to /outputs/{sku}/cutout.png

## Step 2: Generate Background Variations
For each background style in the config:
- Use Firefly generate_image for the background
- Composite the product cutout onto the background
- Match lighting and shadows appropriately
- Save to /outputs/{sku}/bg-{style}.png

## Step 3: Size Variants
For each output size in the config:
- Resize/crop the hero image appropriately
- Use Firefly expand_image if aspect ratio change needed
- Optimize for web (webp format)
- Save to /outputs/{sku}/sizes/{size-name}.webp

## Step 4: Metadata
Generate metadata JSON for each product:
{
    "sku": "...",
    "images": {
        "cutout": "url",
        "backgrounds": {"style": "url", ...},
        "sizes": {"size": "url", ...}
    },
    "processing_time": "...",
    "firefly_seeds": {...}
}

Save manifest to /outputs/batch-${i}-manifest.json
Commit: "Processed batch ${i}: ${PRODUCTS_PER_FORK} products"
EOF
)" &

    # Stagger launches to avoid API rate limits
    sleep 5
done

wait
echo "All $NUM_FORKS batches processing complete!"
```

### Step 3: Per-Product Processing (Inside Each Fork)

```python
# process_product.py - runs inside each sandbox fork
import asyncio
from pathlib import Path
from firefly_sdk import FireflyClient
from PIL import Image
import json

async def process_single_product(product: dict, config: dict):
    """Process a single product through the full pipeline."""
    client = FireflyClient()
    sku = product["sku"]
    category = product["category"]
    source_url = product["image_url"]

    output_dir = Path(f"/outputs/{sku}")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {"sku": sku, "images": {}, "seeds": {}}

    # Step 1: Remove background
    print(f"[{sku}] Removing background...")
    cutout = await client.remove_background(image_url=source_url)
    results["images"]["cutout"] = cutout.url

    # Download cutout for compositing
    cutout_path = output_dir / "cutout.png"
    await download_image(cutout.url, cutout_path)

    # Step 2: Generate backgrounds and composite
    category_config = config["categories"].get(category, config["categories"]["default"])
    bg_styles = category_config["bg_preference"]

    for style in config["background_styles"]:
        if not matches_preference(style["name"], bg_styles):
            continue

        print(f"[{sku}] Generating {style['name']} background...")

        # Generate background
        bg_result = await client.generate_image(
            prompt=style["prompt"],
            content_class="photo",
            width=1200,
            height=1200,
            seed=hash(f"{sku}-{style['name']}") % 1000000  # Reproducible
        )

        results["seeds"][style["name"]] = bg_result.images[0].seed

        # Download and composite
        bg_path = output_dir / f"bg-{style['name']}-raw.png"
        await download_image(bg_result.images[0].url, bg_path)

        # Composite product onto background
        composite_path = output_dir / f"bg-{style['name']}.png"
        await composite_product(
            cutout_path,
            bg_path,
            composite_path,
            expand_ratio=category_config["expand_ratio"],
            shadow_style=category_config["shadow_style"]
        )

        results["images"][f"bg_{style['name']}"] = str(composite_path)

    # Step 3: Generate size variants
    hero_path = output_dir / "bg-studio-white.png"  # Use studio white as hero
    sizes_dir = output_dir / "sizes"
    sizes_dir.mkdir(exist_ok=True)

    for size in config["output_sizes"]:
        print(f"[{sku}] Creating {size['name']} variant...")

        size_path = sizes_dir / f"{size['name']}.webp"

        # Check if aspect ratio change requires expansion
        hero_img = Image.open(hero_path)
        hero_ratio = hero_img.width / hero_img.height
        target_ratio = size["width"] / size["height"]

        if abs(hero_ratio - target_ratio) > 0.1:
            # Need to expand image for different aspect ratio
            expanded = await client.expand_image(
                prompt="continue the background seamlessly",
                image_url=results["images"]["cutout"],
                target_width=size["width"],
                target_height=size["height"]
            )
            await download_and_resize(expanded.images[0].url, size_path, size)
        else:
            # Simple resize
            await resize_image(hero_path, size_path, size["width"], size["height"])

        results["images"][f"size_{size['name']}"] = str(size_path)

    # Save product metadata
    metadata_path = output_dir / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(results, f, indent=2)

    return results


async def process_batch(products: list[dict], config: dict):
    """Process a batch of products."""
    results = []

    for product in products:
        try:
            result = await process_single_product(product, config)
            results.append(result)
        except Exception as e:
            results.append({
                "sku": product["sku"],
                "error": str(e)
            })

    # Save batch manifest
    with open("/outputs/batch-manifest.json", "w") as f:
        json.dump({
            "total": len(products),
            "successful": len([r for r in results if "error" not in r]),
            "failed": len([r for r in results if "error" in r]),
            "products": results
        }, f, indent=2)

    return results
```

### Step 4: Aggregation & CDN Upload

```python
# aggregate_results.py - runs after all forks complete
import asyncio
from e2b import Sandbox

async def aggregate_all_batches(fork_ids: list[str]):
    """Collect results from all sandbox forks and upload to CDN."""
    all_products = []

    for fork_id in fork_ids:
        sandbox = await Sandbox.connect(fork_id)

        # Download batch manifest
        manifest = await sandbox.files.read("/outputs/batch-manifest.json")
        batch_data = json.loads(manifest)

        # Download all product images
        for product in batch_data["products"]:
            if "error" in product:
                continue

            sku = product["sku"]
            product_dir = f"/outputs/{sku}/"

            # Download all images for this product
            files = await sandbox.files.list(product_dir)
            for file in files:
                local_path = f"./aggregated/{sku}/{file['name']}"
                await sandbox.files.download(file["path"], local_path)

            all_products.append(product)

    # Generate master catalog
    master_catalog = {
        "total_products": len(all_products),
        "products": all_products,
        "generated_at": datetime.now().isoformat()
    }

    with open("./aggregated/catalog.json", "w") as f:
        json.dump(master_catalog, f, indent=2)

    # Upload to CDN
    await upload_to_cdn("./aggregated/", "products/")

    return master_catalog
```

## Output Structure

```
/aggregated/
├── catalog.json                    # Master catalog with all SKUs
├── SKU001/
│   ├── cutout.png                  # Transparent background
│   ├── bg-studio-white.png         # Main listing image
│   ├── bg-lifestyle-home.png       # Lifestyle variant
│   ├── bg-lifestyle-office.png     # Lifestyle variant
│   ├── bg-seasonal-summer.png      # Campaign image
│   ├── bg-seasonal-holiday.png     # Campaign image
│   ├── sizes/
│   │   ├── hero.webp               # 1200x1200
│   │   ├── thumbnail.webp          # 400x400
│   │   ├── cart.webp               # 200x200
│   │   ├── social-square.webp      # 1080x1080
│   │   ├── social-story.webp       # 1080x1920
│   │   └── banner.webp             # 1920x600
│   └── metadata.json
├── SKU002/
│   └── ...
└── SKU500/
    └── ...
```

## Performance Metrics

| Metric | Sequential | 10 Parallel Forks |
|--------|-----------|-------------------|
| Products | 500 | 500 |
| Time per product | ~2 min | ~2 min |
| Total time | ~17 hours | ~1.7 hours |
| Firefly API calls | 3,500 | 3,500 (parallelized) |
| Cost efficiency | 1x | 10x faster |

## Advanced Features

### Automatic Quality Check

```python
async def quality_check(product_result: dict) -> dict:
    """Run automated quality checks on processed images."""
    checks = {
        "cutout_clean": await check_cutout_edges(product_result["images"]["cutout"]),
        "background_match": await check_background_consistency(product_result),
        "size_accuracy": await verify_dimensions(product_result),
        "color_accuracy": await check_color_preservation(product_result)
    }

    product_result["quality_score"] = sum(checks.values()) / len(checks)
    product_result["quality_checks"] = checks

    return product_result
```

### Retry Failed Products

```bash
# Reprocess only failed products
jq '[.products[] | select(.error != null)]' aggregated/catalog.json > failed.json

uv run obox <repo> --prompt "Reprocess failed products: $(cat failed.json)"
```

## Use Cases

1. **New Product Launch** - Process entire new collection overnight
2. **Seasonal Updates** - Generate holiday backgrounds for full catalog
3. **A/B Testing** - Create multiple background variants for conversion testing
4. **Platform Expansion** - Generate size variants for new marketplace requirements
5. **Brand Refresh** - Update all product imagery with new visual style
