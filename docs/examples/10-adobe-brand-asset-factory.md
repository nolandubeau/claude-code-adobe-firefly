# Adobe Brand Asset Factory

An automated pipeline for generating brand-compliant creative assets at scale, combining Firefly's commercially-safe generation with Bencium design skills and E2B parallel execution.

## Scenario

Adobe's internal marketing team needs to produce consistent brand assets across:
- 8 product lines (Photoshop, Illustrator, Premiere, After Effects, Lightroom, Firefly, Express, Acrobat)
- 12 campaign themes per year
- 6 asset types (social, email, web, print, video, presentation)
- 15 regional markets

**Challenge**: 8 × 12 × 6 × 15 = **8,640 unique assets per year**

**Solution**: A brand asset factory that generates compliant assets on-demand using parallel sandbox execution.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Adobe Brand Asset Factory                        │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
┌─────────────────────────────────┼───────────────────────────────────┐
│                         Brand Compliance Layer                       │
│  • Color validation (#FA0F00, product-specific palettes)            │
│  • Typography enforcement (Adobe Clean)                              │
│  • Logo placement rules                                              │
│  • Accessibility checks (WCAG 2.1 AA)                               │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────────────┐
        │                         │                                 │
        ▼                         ▼                                 ▼
┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
│  Product Fork     │   │  Campaign Fork    │   │  Regional Fork    │
│  Photoshop        │   │  "AI Revolution"  │   │  EMEA             │
├───────────────────┤   ├───────────────────┤   ├───────────────────┤
│ Firefly prompts:  │   │ Theme tokens:     │   │ Localization:     │
│ • Photo editing   │   │ • Innovation      │   │ • DE, FR, UK      │
│ • Retouching      │   │ • Future-forward  │   │ • Cultural adapt  │
│ • Compositing     │   │ • Bold colors     │   │ • Format sizes    │
└───────────────────┘   └───────────────────┘   └───────────────────┘
```

## Brand Token System

### Core Brand Tokens

```python
# adobe_brand_tokens.py
ADOBE_CORE_BRAND = {
    "mission": "Changing The World Through Digital Experiences",
    "voice": {
        "primary": ["Consistently Innovative", "Authentically Engaging"],
        "secondary": ["Boldly Visionary", "Strategically Inclusive"],
        "avoid": ["vague", "overly technical", "impersonal", "dismissive"]
    },
    "colors": {
        "adobe_red": "#FA0F00",
        "black": "#000000",
        "white": "#FFFFFF",
        "gray_100": "#F5F5F5",
        "gray_900": "#2C2C2C"
    },
    "typography": {
        "primary": "Adobe Clean",
        "secondary": "Adobe Clean Serif",
        "mono": "Source Code Pro",
        "weights": ["Light", "Regular", "Bold", "Black"]
    },
    "imagery": {
        "style": "Innovative, empowering, inclusive",
        "content_class": "photo",  # Default to photorealistic
        "negative_prompts": [
            "generic stock photo",
            "dated technology",
            "exclusionary imagery",
            "cluttered composition"
        ]
    }
}

# Product-specific brand extensions
PRODUCT_BRAND_TOKENS = {
    "photoshop": {
        "color_accent": "#31A8FF",  # Photoshop Blue
        "icon": "Ps",
        "tagline": "The world's best imaging and graphic design software",
        "audience": "photographers, designers, digital artists",
        "firefly_context": [
            "photo editing workflow",
            "professional retouching",
            "creative compositing",
            "layer-based editing"
        ]
    },
    "illustrator": {
        "color_accent": "#FF9A00",  # Illustrator Orange
        "icon": "Ai",
        "tagline": "The industry-standard vector graphics software",
        "audience": "illustrators, brand designers, icon creators",
        "firefly_context": [
            "vector illustration",
            "logo design",
            "typography art",
            "scalable graphics"
        ]
    },
    "premiere": {
        "color_accent": "#9999FF",  # Premiere Purple
        "icon": "Pr",
        "tagline": "Video editing that's always a cut above",
        "audience": "video editors, filmmakers, content creators",
        "firefly_context": [
            "video production",
            "film editing suite",
            "color grading workspace",
            "timeline editing"
        ]
    },
    "firefly": {
        "color_accent": "#FF6B00",  # Firefly Gradient Start
        "color_secondary": "#FF0099",  # Firefly Gradient End
        "icon": "Ff",
        "tagline": "AI-powered creativity, commercially safe",
        "audience": "all creatives, marketers, enterprises",
        "firefly_context": [
            "AI image generation",
            "creative AI assistant",
            "generative fill",
            "style transfer"
        ]
    },
    "lightroom": {
        "color_accent": "#31A8FF",  # Lightroom Blue
        "icon": "Lr",
        "tagline": "Photo editing and organizing made easy",
        "audience": "photographers, photo enthusiasts",
        "firefly_context": [
            "photo organization",
            "batch editing",
            "color correction",
            "photo library"
        ]
    },
    "after_effects": {
        "color_accent": "#9999FF",  # After Effects Purple
        "icon": "Ae",
        "tagline": "Industry-standard motion graphics and visual effects",
        "audience": "motion designers, VFX artists",
        "firefly_context": [
            "motion graphics",
            "visual effects",
            "animation workspace",
            "compositing"
        ]
    },
    "express": {
        "color_accent": "#FF0099",  # Express Pink
        "icon": "Ex",
        "tagline": "Quick and easy content creation for everyone",
        "audience": "social media managers, small businesses, students",
        "firefly_context": [
            "quick content creation",
            "social media templates",
            "easy design tools",
            "drag and drop"
        ]
    },
    "acrobat": {
        "color_accent": "#EC1C24",  # Acrobat Red
        "icon": "Ac",
        "tagline": "The complete PDF solution",
        "audience": "business professionals, legal, education",
        "firefly_context": [
            "document workflow",
            "PDF editing",
            "digital signatures",
            "document collaboration"
        ]
    }
}
```

### Campaign Theme Tokens

```python
CAMPAIGN_THEMES = {
    "ai_revolution": {
        "name": "AI Revolution",
        "period": "Q4 2025",
        "message": "AI that amplifies human creativity",
        "visual_style": {
            "mood": "futuristic, optimistic, collaborative",
            "colors": ["#FF6B00", "#FF0099", "#9999FF"],  # Firefly gradient
            "imagery_keywords": [
                "human and AI collaboration",
                "creative breakthrough",
                "innovation visualization",
                "neural network aesthetic"
            ]
        },
        "firefly_style_presets": ["innovative", "tech-forward", "vibrant"]
    },
    "creator_economy": {
        "name": "Creator Economy",
        "period": "Q1 2026",
        "message": "Every creator deserves professional tools",
        "visual_style": {
            "mood": "empowering, accessible, diverse",
            "colors": ["#FF9A00", "#31A8FF", "#FA0F00"],
            "imagery_keywords": [
                "diverse creators",
                "content creation",
                "social media success",
                "entrepreneurial spirit"
            ]
        },
        "firefly_style_presets": ["lifestyle", "authentic", "energetic"]
    },
    "enterprise_scale": {
        "name": "Enterprise Scale",
        "period": "Q2 2026",
        "message": "Creative workflows that scale with your business",
        "visual_style": {
            "mood": "professional, efficient, powerful",
            "colors": ["#2C2C2C", "#FA0F00", "#F5F5F5"],
            "imagery_keywords": [
                "enterprise collaboration",
                "team workflows",
                "scalable solutions",
                "business success"
            ]
        },
        "firefly_style_presets": ["corporate", "clean", "professional"]
    }
}
```

## Implementation

### Step 1: Asset Request Intake

```python
# asset_request.py
from dataclasses import dataclass
from typing import Literal

@dataclass
class AssetRequest:
    """Defines a brand asset generation request."""
    product: Literal["photoshop", "illustrator", "premiere", "firefly",
                     "lightroom", "after_effects", "express", "acrobat"]
    campaign: str  # e.g., "ai_revolution"
    asset_type: Literal["social", "email", "web", "print", "video", "presentation"]
    platform: str  # e.g., "twitter", "linkedin", "instagram"
    region: str  # e.g., "en-US", "de-DE", "ja-JP"
    custom_prompt: str | None = None  # Override default messaging

# Example batch request
ASSET_BATCH = [
    AssetRequest("photoshop", "ai_revolution", "social", "twitter", "en-US"),
    AssetRequest("photoshop", "ai_revolution", "social", "linkedin", "en-US"),
    AssetRequest("photoshop", "ai_revolution", "social", "instagram", "en-US"),
    AssetRequest("photoshop", "ai_revolution", "email", "customer", "en-US"),
    AssetRequest("photoshop", "ai_revolution", "web", "landing", "en-US"),
    # ... more requests
]
```

### Step 2: Launch Parallel Asset Generation

```bash
# Generate assets for all Photoshop AI Revolution campaign assets
cd apps/sandbox_workflows

uv run obox https://github.com/adobe/brand-asset-factory.git \
  --branch assets/photoshop-ai-revolution \
  --model opus \
  --forks 6 \
  --prompt "$(cat <<'EOF'
You are generating brand-compliant assets for Adobe Photoshop's "AI Revolution" campaign.

BRAND CONTEXT:
- Product: Photoshop (accent color: #31A8FF)
- Campaign: AI Revolution (AI that amplifies human creativity)
- Adobe Voice: Consistently Innovative, Authentically Engaging

FORK ASSIGNMENTS:
Fork 1: Twitter assets (1200x675, 1200x1200)
Fork 2: LinkedIn assets (1200x627, 1200x1200)
Fork 3: Instagram assets (1080x1080, 1080x1920 stories)
Fork 4: Email headers and CTAs (600px wide, responsive)
Fork 5: Web banners and hero images (1920x1080, 2560x1440)
Fork 6: Presentation slides (16:9, 1920x1080)

FOR EACH FORK:

1. Use bencium-controlled-ux-designer skill for layout and composition
2. Generate hero imagery with Firefly:
   - Content class: photo
   - Style: innovative, futuristic, collaborative human-AI
   - Include Photoshop UI context where appropriate
   - Apply product accent color (#31A8FF) in design elements

3. Create 3 variations per asset size:
   - Variation A: Feature-focused (AI Assistant announcement)
   - Variation B: Workflow-focused (creative process)
   - Variation C: Result-focused (stunning output showcase)

4. Apply brand compliance:
   - Adobe Red (#FA0F00) for CTAs
   - Adobe Clean typography
   - Consistent logo placement (bottom-right or top-left)
   - WCAG 2.1 AA contrast ratios

5. Generate copy aligned with brand voice:
   - Headlines: Bold, innovative, benefit-focused
   - Body: Clear, engaging, actionable
   - CTAs: Direct, value-driven

OUTPUT: /outputs/{platform}/{variation}/
EOF
)"
```

### Step 3: Product-Specific Firefly Prompts

```python
# firefly_prompt_builder.py
def build_product_prompt(product: str, campaign: str, context: str) -> str:
    """Build brand-compliant Firefly prompt for product asset."""

    product_tokens = PRODUCT_BRAND_TOKENS[product]
    campaign_tokens = CAMPAIGN_THEMES[campaign]

    base_prompt = f"""
    Professional marketing image for Adobe {product.title()}.

    Scene: {', '.join(product_tokens['firefly_context'][:2])}
    Mood: {campaign_tokens['visual_style']['mood']}
    Visual elements: {', '.join(campaign_tokens['visual_style']['imagery_keywords'][:2])}

    Style: {', '.join(campaign_tokens['firefly_style_presets'])}
    Color accent: {product_tokens['color_accent']}

    Context: {context}

    High quality, professional photography, modern aesthetic,
    Adobe brand style, innovative and empowering.
    """

    return base_prompt.strip()

# Example usage in sandbox agent
prompts = {
    "photoshop_hero": build_product_prompt(
        "photoshop",
        "ai_revolution",
        "Creative professional using AI Assistant to enhance portrait photo"
    ),
    "illustrator_hero": build_product_prompt(
        "illustrator",
        "ai_revolution",
        "Vector artist creating stunning logo with AI-powered tools"
    ),
    "firefly_hero": build_product_prompt(
        "firefly",
        "ai_revolution",
        "Magical transformation of text prompt into photorealistic image"
    )
}
```

### Step 4: Bencium Skill Integration

#### Social Media Cards (bencium-controlled)

```
Use the bencium-controlled-ux-designer skill:

"Design a Twitter announcement card for Photoshop AI Assistant.

 Brand Requirements:
 - Adobe Red (#FA0F00) for primary CTA
 - Photoshop Blue (#31A8FF) for accent elements
 - Adobe Clean font family
 - 1200x675 dimensions

 Content:
 - Headline: 'Meet Your Creative Partner'
 - Subhead: 'AI Assistant in Photoshop handles complex tasks so you can focus on creativity'
 - CTA: 'Try Now in Photoshop'
 - Badge: 'NEW at MAX 2025'

 Layout should be clean, professional, with clear visual hierarchy.
 Hero image area should accommodate Firefly-generated imagery.
 Include subtle Photoshop UI elements to ground the product context."
```

#### Landing Page Section (bencium-innovative)

```
Use the bencium-innovative-ux-designer skill:

"Design a bold hero section for Firefly's AI Revolution landing page.

 This should feel like a breakthrough moment in creative technology.
 Push beyond typical software marketing—make it feel like magic.

 Elements:
 - Full-bleed hero image (Firefly-generated, human-AI collaboration)
 - Floating prompt input field demonstrating text-to-image
 - Animated particles/glow effects suggesting AI generation
 - Bold headline: 'Your Imagination, Amplified'
 - Gradient using Firefly colors (#FF6B00 → #FF0099)

 The design should embody Adobe's brand voice:
 'Boldly Visionary' while remaining 'Authentically Engaging'

 Make visitors feel the creative potential before they even try the product."
```

## Output Structure

```
/brand-asset-factory/
├── config/
│   ├── brand-tokens.json         # Core brand definitions
│   ├── product-tokens.json       # Product-specific extensions
│   └── campaign-themes.json      # Active campaign definitions
├── templates/
│   ├── social/
│   │   ├── twitter-card.html
│   │   ├── linkedin-post.html
│   │   └── instagram-grid.html
│   ├── email/
│   │   └── announcement.html
│   └── web/
│       └── hero-section.html
├── outputs/
│   ├── photoshop/
│   │   ├── ai_revolution/
│   │   │   ├── social/
│   │   │   │   ├── twitter/
│   │   │   │   │   ├── variation-a.png
│   │   │   │   │   ├── variation-b.png
│   │   │   │   │   └── variation-c.png
│   │   │   │   ├── linkedin/
│   │   │   │   └── instagram/
│   │   │   ├── email/
│   │   │   ├── web/
│   │   │   └── presentation/
│   │   └── creator_economy/
│   ├── illustrator/
│   ├── premiere/
│   ├── firefly/
│   └── ... (other products)
├── localized/
│   ├── de-DE/
│   ├── fr-FR/
│   ├── ja-JP/
│   └── zh-CN/
└── compliance/
    ├── accessibility-report.json
    ├── brand-validation.json
    └── asset-manifest.json
```

## Scaling with E2B Forks

### Full Product Line Generation

```bash
# Generate assets for ALL 8 products simultaneously
PRODUCTS=("photoshop" "illustrator" "premiere" "after_effects"
          "lightroom" "firefly" "express" "acrobat")

for product in "${PRODUCTS[@]}"; do
  uv run obox https://github.com/adobe/brand-asset-factory.git \
    --branch "assets/${product}-ai-revolution" \
    --model sonnet \
    --forks 6 \
    --prompt "Generate AI Revolution campaign assets for Adobe ${product^}" &
done

wait  # All 48 forks run in parallel (8 products × 6 asset types)
```

### Regional Localization Pass

```bash
# After EN-US assets are complete, localize to all regions
REGIONS=("de-DE" "fr-FR" "es-ES" "it-IT" "pt-BR" "ja-JP" "ko-KR" "zh-CN" "zh-TW")

uv run obox https://github.com/adobe/brand-asset-factory.git \
  --branch "localization/batch-1" \
  --model sonnet \
  --forks 9 \
  --prompt "Localize EN-US assets to assigned region. Adapt imagery for cultural relevance using Firefly."
```

## Metrics and Compliance

### Brand Compliance Validation

```python
# compliance_checker.py
async def validate_asset(asset_path: str, product: str) -> dict:
    """Validate asset against brand guidelines."""

    checks = {
        "color_compliance": check_brand_colors(asset_path, product),
        "typography_compliance": check_fonts(asset_path),
        "logo_placement": check_logo_rules(asset_path),
        "accessibility": check_wcag_aa(asset_path),
        "resolution": check_minimum_resolution(asset_path),
        "aspect_ratio": check_aspect_ratio(asset_path)
    }

    return {
        "asset": asset_path,
        "passed": all(checks.values()),
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }
```

### Generation Metrics

| Metric | Traditional | Brand Asset Factory |
|--------|------------|---------------------|
| Assets per day | 20-30 | 500+ |
| Time to market | 2-3 weeks | 24-48 hours |
| Brand consistency | Variable | 98%+ (automated validation) |
| Localization time | 1 week per region | All regions in parallel |
| Cost per asset | $50-200 (agency) | $0.50-2.00 (AI generation) |

## Integration with Adobe DAM

Generated assets automatically sync to Adobe Experience Manager:

```python
# dam_sync.py
async def sync_to_aem(asset_batch: list[str], metadata: dict):
    """Push generated assets to Adobe Experience Manager."""

    for asset_path in asset_batch:
        await aem_client.upload(
            file=asset_path,
            folder=f"/content/dam/adobe/campaigns/{metadata['campaign']}/{metadata['product']}",
            metadata={
                "dc:title": metadata["title"],
                "dc:description": metadata["description"],
                "adobe:product": metadata["product"],
                "adobe:campaign": metadata["campaign"],
                "adobe:region": metadata["region"],
                "adobe:assetType": metadata["asset_type"],
                "adobe:generatedBy": "brand-asset-factory",
                "adobe:fireflyModel": "image-model-5"
            }
        )
```

This creates a closed-loop creative production system: **Request → Generate → Validate → Publish → Measure → Optimize**.
