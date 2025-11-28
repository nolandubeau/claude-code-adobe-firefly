# A/B Landing Page Generation at Scale

Generate multiple complete landing page variants simultaneously for A/B testing, each with unique AI-generated imagery and design treatments.

## Scenario

A SaaS company launching a new product needs 8 landing page variants to A/B test:
- 2 hero image styles (photo vs. illustration)
- 2 color schemes (brand blue vs. energetic orange)
- 2 layout patterns (hero-focused vs. feature-grid)

Instead of creating sequentially, generate all 8 in parallel sandboxes.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Orchestrator: Generate 8 Landing Page Variants                 │
│  Matrix: 2 styles × 2 colors × 2 layouts = 8 variants           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │         │         │         │         │
        ▼         ▼         ▼         ▼         ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
   │ Fork 1  │ │ Fork 2  │ │ Fork 3  │ │ Fork 4  │
   │ photo   │ │ photo   │ │ illust  │ │ illust  │
   │ blue    │ │ orange  │ │ blue    │ │ orange  │
   │ hero    │ │ hero    │ │ hero    │ │ hero    │
   └─────────┘ └─────────┘ └─────────┘ └─────────┘
        │         │         │         │
        ▼         ▼         ▼         ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
   │ Fork 5  │ │ Fork 6  │ │ Fork 7  │ │ Fork 8  │
   │ photo   │ │ photo   │ │ illust  │ │ illust  │
   │ blue    │ │ orange  │ │ blue    │ │ orange  │
   │ grid    │ │ grid    │ │ grid    │ │ grid    │
   └─────────┘ └─────────┘ └─────────┘ └─────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │  Deploy to A/B Testing  │
              │  Infrastructure         │
              └─────────────────────────┘
```

## Implementation

### Step 1: Define Variant Matrix

```python
# variant_matrix.py
from itertools import product

IMAGE_STYLES = [
    {
        "name": "photo",
        "firefly_content_class": "photo",
        "prompts": {
            "hero": "professional team collaborating on modern software, natural lighting, premium office space",
            "feature1": "person using laptop with dashboard on screen, clean desk setup, soft lighting",
            "feature2": "diverse team high-fiving, celebration moment, bright modern office",
            "testimonial_bg": "abstract soft gradient background, professional, subtle texture"
        }
    },
    {
        "name": "illustration",
        "firefly_content_class": "art",
        "prompts": {
            "hero": "isometric 3D illustration of SaaS platform, floating UI elements, vibrant colors",
            "feature1": "flat design illustration of analytics dashboard, data visualization, clean lines",
            "feature2": "character illustration team collaboration, friendly style, diverse characters",
            "testimonial_bg": "geometric pattern background, soft colors, abstract shapes"
        }
    }
]

COLOR_SCHEMES = [
    {
        "name": "brand-blue",
        "primary": "#2563EB",
        "secondary": "#3B82F6",
        "accent": "#60A5FA",
        "background": "#F8FAFC",
        "text": "#1E293B"
    },
    {
        "name": "energetic-orange",
        "primary": "#EA580C",
        "secondary": "#F97316",
        "accent": "#FB923C",
        "background": "#FFFBEB",
        "text": "#292524"
    }
]

LAYOUTS = [
    {
        "name": "hero-focused",
        "sections": ["hero-large", "social-proof", "features-3col", "testimonials", "cta"],
        "skill": "bencium-innovative-ux-designer"
    },
    {
        "name": "feature-grid",
        "sections": ["hero-compact", "feature-grid-6", "comparison", "testimonials", "pricing", "cta"],
        "skill": "bencium-controlled-ux-designer"
    }
]

# Generate all combinations
VARIANTS = [
    {
        "id": f"v{i+1}",
        "image_style": img,
        "color_scheme": color,
        "layout": layout
    }
    for i, (img, color, layout) in enumerate(
        product(IMAGE_STYLES, COLOR_SCHEMES, LAYOUTS)
    )
]
```

### Step 2: Launch Parallel Generation

```bash
#!/bin/bash
# generate_variants.sh

# Generate variant configurations
python variant_matrix.py > /tmp/variants.json

# Launch 8 parallel sandbox forks
cd apps/sandbox_workflows

for variant in $(cat /tmp/variants.json | jq -c '.[]'); do
    id=$(echo $variant | jq -r '.id')
    style=$(echo $variant | jq -r '.image_style.name')
    color=$(echo $variant | jq -r '.color_scheme.name')
    layout=$(echo $variant | jq -r '.layout.name')

    uv run obox https://github.com/your-org/landing-page-template.git \
        --branch "variant-${id}" \
        --model sonnet \
        --prompt "$(cat <<EOF
Generate landing page variant: ${id}

IMAGE STYLE: ${style}
- Content class: $(echo $variant | jq -r '.image_style.firefly_content_class')
- Generate these images with Firefly:
  $(echo $variant | jq -r '.image_style.prompts | to_entries | map("  - \(.key): \(.value)") | join("\n")')

COLOR SCHEME: ${color}
$(echo $variant | jq -r '.color_scheme | to_entries | map("  - \(.key): \(.value)") | join("\n")')

LAYOUT: ${layout}
- Sections: $(echo $variant | jq -r '.layout.sections | join(", ")')
- Use skill: $(echo $variant | jq -r '.layout.skill')

Tasks:
1. Generate all hero and feature images with Firefly
2. Apply color scheme to Tailwind config
3. Build all sections as React components
4. Create responsive layouts (mobile, tablet, desktop)
5. Export to /dist/ with all assets
6. Take screenshots at each breakpoint
7. Commit with message: "Landing page variant ${id}: ${style}/${color}/${layout}"
EOF
)" &
done

wait
echo "All 8 variants generated!"
```

### Step 3: Automated Image Generation Per Fork

Each sandbox runs this Firefly workflow:

```typescript
// Inside each sandbox fork
import { FireflyClient } from './firefly';

async function generateVariantImages(variant: Variant) {
    const client = new FireflyClient();
    const images = {};

    // Generate hero image
    const heroResult = await client.generateImage({
        prompt: variant.imageStyle.prompts.hero,
        contentClass: variant.imageStyle.fireflyContentClass,
        width: 1920,
        height: 1080,
        aspectRatio: "16:9"
    });
    images.hero = heroResult.images[0].url;

    // Generate feature images
    for (const [key, prompt] of Object.entries(variant.imageStyle.prompts)) {
        if (key !== 'hero') {
            const result = await client.generateImage({
                prompt,
                contentClass: variant.imageStyle.fireflyContentClass,
                width: 800,
                height: 600
            });
            images[key] = result.images[0].url;
        }
    }

    // Apply style transfer for consistency
    const styledImages = {};
    for (const [key, url] of Object.entries(images)) {
        if (key !== 'hero') {
            const styled = await client.applyStyleTransfer({
                prompt: `${variant.imageStyle.prompts[key]}, consistent with brand style`,
                styleImageUrl: images.hero,
                styleStrength: 0.6
            });
            styledImages[key] = styled.images[0].url;
        }
    }

    return { ...images, ...styledImages };
}
```

### Step 4: Collect & Deploy Results

```python
# deploy_variants.py
import asyncio
from e2b import Sandbox

async def collect_and_deploy():
    variants = []

    # Collect from all forks
    for fork_id in get_completed_forks():
        sandbox = await Sandbox.connect(fork_id)

        # Get built assets
        dist = await sandbox.files.download("/dist/")

        # Get screenshots
        screenshots = await sandbox.files.list("/screenshots/")

        # Get variant config
        config = await sandbox.files.read("/variant-config.json")

        variants.append({
            "id": config["id"],
            "dist_path": dist,
            "screenshots": screenshots,
            "config": config
        })

    # Deploy each variant to A/B testing infrastructure
    for variant in variants:
        deploy_to_ab_platform(
            variant_id=variant["id"],
            assets=variant["dist_path"],
            config={
                "traffic_percentage": 100 / len(variants),
                "metrics": ["conversion", "bounce_rate", "time_on_page"]
            }
        )

    # Generate comparison report
    report = generate_comparison_report(variants)
    print(report)
```

## Output Per Variant

```
/variant-v1/
├── dist/
│   ├── index.html
│   ├── assets/
│   │   ├── hero.webp           # Firefly generated, optimized
│   │   ├── feature1.webp       # Firefly generated
│   │   ├── feature2.webp       # Firefly generated
│   │   └── testimonial-bg.webp # Firefly generated
│   ├── css/
│   │   └── styles.css          # Tailwind with color scheme
│   └── js/
│       └── main.js
├── screenshots/
│   ├── mobile-375.png
│   ├── tablet-768.png
│   └── desktop-1440.png
├── variant-config.json
└── lighthouse-report.json
```

## Comparison Dashboard

After generation, view all variants side-by-side:

```markdown
# Landing Page Variants Comparison

| Variant | Style | Colors | Layout | Hero Preview | Mobile Score |
|---------|-------|--------|--------|--------------|--------------|
| v1 | photo | blue | hero | ![](v1/hero.png) | 95 |
| v2 | photo | orange | hero | ![](v2/hero.png) | 94 |
| v3 | illust | blue | hero | ![](v3/hero.png) | 96 |
| v4 | illust | orange | hero | ![](v4/hero.png) | 95 |
| v5 | photo | blue | grid | ![](v5/hero.png) | 93 |
| v6 | photo | orange | grid | ![](v6/hero.png) | 92 |
| v7 | illust | blue | grid | ![](v7/hero.png) | 94 |
| v8 | illust | orange | grid | ![](v8/hero.png) | 93 |
```

## Cost & Time Analysis

| Metric | Sequential | 8 Parallel Sandboxes |
|--------|-----------|---------------------|
| Total time | ~4 hours | ~30 minutes |
| Firefly API calls | 32 (4 per variant) | 32 (same, parallelized) |
| Designer hours | 16+ hours | 1 hour (review) |
| Iteration cycles | Limited | Test all at once |

## Use Cases

1. **Product Launch** - Test multiple value propositions simultaneously
2. **Seasonal Campaigns** - Generate holiday variants in parallel
3. **Market Segmentation** - Create variants for different audiences
4. **Rebrand Testing** - Explore new brand directions safely
5. **Localization** - Generate region-specific imagery and layouts
