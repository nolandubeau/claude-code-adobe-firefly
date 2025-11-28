# Parallel Design Exploration with Sandbox Forks

Scale design brainstorming by running multiple creative directions simultaneously across isolated E2B sandboxes.

## Scenario

A startup needs to redesign their app's onboarding flow. Instead of exploring one direction at a time, launch 4 parallel sandboxes to explore different design philosophies simultaneously.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Main Claude Code Session                                   │
│  "Design 4 variations of onboarding flow"                   │
└─────────────────────────────┬───────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Sandbox Fork 1 │ │  Sandbox Fork 2 │ │  Sandbox Fork 3 │
│  "Minimalist"   │ │  "Playful"      │ │  "Professional" │
│                 │ │                 │ │                 │
│ • bencium-      │ │ • bencium-      │ │ • bencium-      │
│   controlled    │ │   innovative    │ │   controlled    │
│ • Firefly:      │ │ • Firefly:      │ │ • Firefly:      │
│   clean icons   │ │   vibrant art   │ │   corporate     │
└─────────────────┘ └─────────────────┘ └─────────────────┘
              │               │               │
              └───────────────┼───────────────┘
                              ▼
                    ┌─────────────────┐
                    │  Compare & Vote │
                    │  on Results     │
                    └─────────────────┘
```

## Implementation

### Step 1: Define Design Directions

```python
# design_directions.py
DESIGN_DIRECTIONS = [
    {
        "name": "minimalist",
        "skill": "bencium-controlled-ux-designer",
        "firefly_style": "photo",
        "description": "Clean, whitespace-focused, single accent color",
        "firefly_prompts": [
            "minimal geometric abstract background, soft gradients, clean lines",
            "simple line art icon set, onboarding illustration, white background",
            "abstract flowing shapes, pastel colors, modern minimal design"
        ]
    },
    {
        "name": "playful",
        "skill": "bencium-innovative-ux-designer",
        "firefly_style": "art",
        "description": "Bold colors, illustrations, friendly characters",
        "firefly_prompts": [
            "cheerful cartoon character waving, friendly onboarding mascot, vibrant colors",
            "playful abstract shapes pattern, colorful confetti, celebration mood",
            "whimsical hand-drawn style illustration, welcome scene, warm colors"
        ]
    },
    {
        "name": "professional",
        "skill": "bencium-controlled-ux-designer",
        "firefly_style": "photo",
        "description": "Corporate, trustworthy, data-driven visuals",
        "firefly_prompts": [
            "professional business team collaboration, modern office, natural lighting",
            "abstract data visualization, blue corporate colors, clean tech aesthetic",
            "confident professional using tablet, enterprise software, premium feel"
        ]
    },
    {
        "name": "bold-experimental",
        "skill": "bencium-innovative-ux-designer",
        "firefly_style": "art",
        "description": "Cutting-edge, unconventional layouts, striking visuals",
        "firefly_prompts": [
            "futuristic neon abstract art, cyberpunk aesthetic, bold contrasts",
            "experimental 3D typography, avant-garde design, dark background",
            "surreal digital landscape, impossible geometry, vivid colors"
        ]
    }
]
```

### Step 2: Launch Parallel Sandbox Forks

```bash
# Launch 4 parallel design explorations
cd apps/sandbox_workflows

uv run obox https://github.com/your-org/app-redesign.git \
  --branch feature/onboarding-redesign \
  --model opus \
  --forks 4 \
  --prompt "$(cat <<'EOF'
You are designing an onboarding flow variation.

DIRECTION: {direction_name}
SKILL: Use the {skill} skill for all design decisions
STYLE: {description}

Tasks:
1. Use Firefly to generate 3 hero images with these prompts:
   {firefly_prompts}

2. Design a 4-screen onboarding flow:
   - Welcome screen with generated hero image
   - Feature highlight 1
   - Feature highlight 2
   - Get started CTA

3. Create the components in React + Tailwind
4. Save screenshots of each screen to /outputs/

Commit your work with message: "Design exploration: {direction_name}"
EOF
)"
```

### Step 3: Aggregate Results

After all forks complete, collect the outputs:

```python
# aggregate_designs.py
import asyncio
from pathlib import Path

async def collect_fork_results(fork_ids: list[str]):
    """Collect design outputs from all sandbox forks."""
    results = []

    for fork_id in fork_ids:
        # Download outputs from each sandbox
        sandbox = await get_sandbox(fork_id)

        # Get generated images
        images = await sandbox.files.list("/outputs/")

        # Get component code
        components = await sandbox.files.read("/src/components/Onboarding/")

        results.append({
            "fork_id": fork_id,
            "images": images,
            "components": components,
            "branch": f"design-{fork_id[:8]}"
        })

    return results

async def create_comparison_report(results):
    """Generate side-by-side comparison."""
    report = "# Design Exploration Results\n\n"

    for r in results:
        report += f"## {r['direction']}\n"
        report += f"Branch: `{r['branch']}`\n\n"
        report += "### Generated Images\n"
        for img in r['images']:
            report += f"![{img['name']}]({img['url']})\n"
        report += "\n---\n\n"

    return report
```

## Workflow Commands

### Quick Start

```bash
# From project root
/prime_obox

# Then run the exploration
uv run obox <repo> --forks 4 --prompt "Explore 4 onboarding design directions using bencium skills and Firefly imagery"
```

### Using Claude Code Directly

```
# In Claude Code session:

1. "Use the bencium-innovative-ux-designer skill to design a playful onboarding flow"

2. "Generate hero images with Firefly: cheerful welcome illustration, vibrant colors, friendly mascot"

3. "Create React components for the 4-screen onboarding"

4. "Fork this to a new sandbox and try a minimalist approach instead"
```

## Example Output Structure

Each sandbox fork produces:

```
/outputs/
├── direction-config.json       # Design direction metadata
├── hero-images/
│   ├── welcome-hero.png       # Firefly generated
│   ├── feature-1-bg.png       # Firefly generated
│   └── feature-2-bg.png       # Firefly generated
├── screenshots/
│   ├── screen-1-welcome.png
│   ├── screen-2-feature.png
│   ├── screen-3-feature.png
│   └── screen-4-cta.png
├── components/
│   ├── OnboardingFlow.tsx
│   ├── WelcomeScreen.tsx
│   ├── FeatureScreen.tsx
│   └── CTAScreen.tsx
└── design-tokens.json          # Colors, typography, spacing
```

## Benefits of Parallel Exploration

| Traditional | Parallel Sandboxes |
|-------------|-------------------|
| 4 hours for 4 directions | 1 hour for 4 directions |
| Sequential iteration | Simultaneous exploration |
| Designer fatigue | Fresh perspective each fork |
| Single context | Isolated experiments |
| Hard to compare | Easy side-by-side review |

## Integration Points

### Firefly Tools Used
- `generate_image` - Hero images, backgrounds, illustrations
- `apply_style_transfer` - Consistent visual style across screens
- `expand_image` - Extend backgrounds for responsive layouts

### Bencium Skills Used
- `bencium-controlled-ux-designer` - Minimalist, professional directions
- `bencium-innovative-ux-designer` - Playful, experimental directions

### Sandbox Capabilities
- Full Node.js environment for React development
- Isolated file systems per fork
- Git branches for each direction
- Parallel execution across forks
