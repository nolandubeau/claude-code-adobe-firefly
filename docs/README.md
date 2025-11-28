# Bencium UX Designer Skills + Adobe Firefly Integration

This documentation covers the UX Designer skills and their integration with Adobe Firefly for complete creative workflows.

## Integration Examples

See the `examples/` folder for complete integration patterns:

### Basic Integrations

| Example | Description | Skills Used |
|---------|-------------|-------------|
| [01-saas-landing-page.md](examples/01-saas-landing-page.md) | SaaS landing page with AI-generated hero imagery | bencium-innovative-ux-designer + Firefly |
| [02-product-showcase.md](examples/02-product-showcase.md) | E-commerce product page with product photography pipeline | bencium-controlled-ux-designer + Firefly |
| [03-creative-portfolio.md](examples/03-creative-portfolio.md) | Bold agency portfolio with layered visual assets | bencium-innovative-ux-designer + Firefly |
| [04-dashboard-app.md](examples/04-dashboard-app.md) | Analytics dashboard with custom illustrations | bencium-controlled-ux-designer + Firefly |

### Scaled Workflows (E2B Sandboxes)

These examples combine the parallel execution power of E2B sandboxes with Bencium design skills and Firefly image generation:

| Example | Description | Capabilities |
|---------|-------------|--------------|
| [05-parallel-design-exploration.md](examples/05-parallel-design-exploration.md) | Explore 4+ design directions simultaneously | 4 forks × different design philosophies |
| [06-ab-landing-page-scale.md](examples/06-ab-landing-page-scale.md) | Generate 8 A/B test variants in parallel | 8 forks × style/color/layout matrix |
| [07-brand-identity-exploration.md](examples/07-brand-identity-exploration.md) | Create 5 complete brand systems simultaneously | 5 forks × full brand books with assets |
| [08-product-photography-pipeline.md](examples/08-product-photography-pipeline.md) | Process 500 products with background generation | 10 forks × 50 products each |

### Why Parallel Sandboxes?

| Traditional | Parallel Sandboxes |
|-------------|-------------------|
| 1 design at a time | 4-10 designs simultaneously |
| Sequential iteration | Explore all options at once |
| Hours per variant | Minutes per variant |
| Designer bottleneck | AI-assisted scaling |
| Limited exploration | Comprehensive coverage |

---

## UX Designer Skills

Two Claude Code skills for UI/UX design guidance — choose based on your project needs.

### Why Two Variants?

| Aspect | Controlled | Innovative |
|--------|------------|------------|
| **Decision Authority** | Asks before making choices | Commits boldly to directions |
| **Aesthetic Philosophy** | Flat, minimal, no shadows | Shadows, gradients, textures allowed |
| **Typography** | 2-3 typefaces, mathematical scales | Experimental, characterful choices |
| **Structure** | 6 files (~3,500 lines) | 6 files (~1,000 lines) |
| **Best For** | Production, enterprise, regulated | Landing pages, portfolios, campaigns |

### Skill Variants

#### bencium-controlled-ux-designer

**Systematic design for production work.**

Best for:

- Enterprise applications
- Healthcare/regulated industries
- Long-term maintainable projects
- Design systems requiring consistency
- Accessibility-critical interfaces

Key behaviors:

- **Always asks** before making design decisions
- WCAG 2.1 AA compliance (non-negotiable)
- Mathematical spacing/typography scales
- Flat, minimal aesthetic (no shadows, gradients, glass)
- Comprehensive validation checklists

```text
bencium-controlled-ux-designer/
├── SKILL.md                  # Main skill (~740 lines)
├── ACCESSIBILITY.md          # Full WCAG guidance (~830 lines)
├── RESPONSIVE-DESIGN.md      # Breakpoints & patterns (~600 lines)
├── DESIGN-SYSTEM-TEMPLATE.md # Project kickoff framework
├── MOTION-SPEC.md            # Animation specifications
└── README.md
```

#### bencium-innovative-ux-designer

**Bold design for creative exploration.**

Inspired by [Anthropic's Frontend Aesthetics Cookbook](https://github.com/anthropics/claude-cookbooks/blob/main/coding/prompting_for_frontend_aesthetics.ipynb).

Best for:

- Landing pages and marketing sites
- Creative agency projects
- Prototypes and concept exploration
- Portfolio pieces
- Short-term campaigns

Key behaviors:

- **Commits boldly** to aesthetic directions (doesn't ask)
- Asks Design Thinking questions upfront, then executes
- Shadows, gradients, textures allowed when intentional
- Typography experimentation encouraged
- Accessibility as baseline (not blocking exploration)

```text
bencium-innovative-ux-designer/
├── SKILL.md                  # Main skill (~700 lines)
├── ACCESSIBILITY.md          # Compressed essentials (~110 lines)
├── RESPONSIVE-DESIGN.md      # Mobile-first basics (~90 lines)
├── MOTION-SPEC.md            # Animation essentials (~70 lines)
└── README.md
```

### Anti-Patterns (Both Variants Avoid)

Both skills are designed to avoid "AI slop" — the generic, forgettable aesthetics that flood AI-generated interfaces:

**Fonts to avoid:**

- Inter, Roboto, Arial as primary typefaces
- Space Grotesk (overused by AI tools)
- System fonts without intention

**Colors to avoid:**

- Generic SaaS blue (`#3B82F6`)
- Purple gradients on white backgrounds
- Teal + coral combinations

**Patterns to avoid:**

- Liquid glass / glassmorphism everywhere
- Apple mimicry without purpose
- Cookie-cutter SaaS layouts
- Predictable component arrangements

### Aesthetic Tone Options (Innovative Variant)

The innovative variant can execute across different aesthetic directions:

| Tone | Characteristics |
|------|-----------------|
| Brutally minimal | Maximum whitespace, single accent, stark typography |
| Maximalist chaos | Dense information, layered elements, controlled overwhelm |
| Retro-futuristic | Nostalgic tech aesthetics, CRT glow, pixel elements |
| Organic/natural | Earthy palettes, hand-drawn elements, asymmetry |
| Luxury/refined | Restrained elegance, premium materials, subtle animation |
| Editorial/magazine | Strong typography hierarchy, dramatic layouts |
| Brutalist/raw | Exposed structure, system fonts as statement, anti-design |
| Soft/pastel | Gentle gradients, rounded forms, approachable |

### Installation

Copy the desired skill folder to your Claude Code skills directory:

```bash
# For controlled/production workflow
cp -r bencium-controlled-ux-designer ~/.claude/skills/

# For creative/innovative workflow
cp -r bencium-innovative-ux-designer ~/.claude/skills/
```

### Example Interactions

#### Controlled Variant

**You:** "I need a call-to-action button for the hero section"

**Claude:** "Before I implement this button, I have design questions:

1. What's the primary action you want to emphasize?
2. Do you have brand colors in mind, or should I suggest options?
3. What emotion should this button convey? (urgent, calm, professional)

I can suggest 3 unique color directions that break from typical patterns..."

#### Innovative Variant

**You:** "I need a call-to-action button for the hero section"

**Claude:** "What's the overall vibe for this project? Options:

- Brutally minimal
- Bold and playful
- Luxury/refined
- Something else?

Once I know the direction, I'll commit to a distinctive button design that avoids generic SaaS patterns."

**You:** "Bold and playful"

**Claude:** *Implements a distinctive button with intentional design choices, no further questions*

### Key Differences Summary

| Scenario | Controlled | Innovative |
|----------|------------|------------|
| Color choice | "Here are 3 options. Which do you prefer?" | "I'm using [X] because it fits the playful tone" |
| Shadow usage | "No shadows per design system" | "Adding subtle shadow for depth and hierarchy" |
| Typography | "Using Inter for readability" | "Using [characterful font] to stand out" |
| Layout | "Following established grid patterns" | "Breaking grid intentionally for visual interest" |

### Version History

- **v2.0.0** (2025-11-22): Split into two variants
  - Created `bencium-controlled-ux-designer` (production focus)
  - Created `bencium-innovative-ux-designer` (creative focus)
  - Innovative variant inspired by Anthropic's Frontend Aesthetics Cookbook
  - Compressed supporting files for innovative variant (~70% reduction)
  - Added Design Thinking Protocol to innovative variant
  - Added aesthetic tone options
- **v1.1.0** (2025-11-20): Comprehensive design system enhancement
- **v1.0.0** (2025-10-18): Initial release

### References

- [Anthropic Frontend Aesthetics Cookbook](https://github.com/anthropics/claude-cookbooks/blob/main/coding/prompting_for_frontend_aesthetics.ipynb)
- [Claude Code Skills Documentation](https://docs.anthropic.com/claude-code/skills)

### License

Personal skills - use and modify as needed for your projects.
