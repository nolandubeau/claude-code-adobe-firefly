# Example 1: SaaS Landing Page with AI-Generated Hero

This example demonstrates combining `bencium-innovative-ux-designer` with Adobe Firefly to create a distinctive SaaS landing page.

## Workflow

### Step 1: Design the Page Structure

Use the bencium-innovative-ux-designer skill:

```
Create a SaaS landing page for a project management tool called "FlowBoard".
The aesthetic should be: Luxury/refined with restrained elegance.
Include: hero section, features grid, pricing cards, and CTA.
```

### Step 2: Generate Hero Imagery

Use Adobe Firefly to generate imagery that matches the design aesthetic:

```
/firefly-generate Abstract flowing gradients representing workflow and productivity, deep navy blues with subtle gold accents, minimalist, elegant, premium feel --style art --size 1920x1080
```

### Step 3: Generate Feature Icons

Create custom illustrated icons:

```
/firefly-generate Minimalist line icon of a kanban board, single color, flat design, professional --style art --size 256x256 --variations 4
```

## Sample Prompts for Integration

### Hero Background Variations

```
# Geometric abstract
/firefly-generate Abstract geometric shapes floating in space, navy and gold color palette, depth and dimension, premium corporate aesthetic --style art

# Organic flow
/firefly-generate Flowing silk ribbons in deep blue and champagne gold, elegant movement, luxury brand aesthetic --style art

# Data visualization inspired
/firefly-generate Abstract network of connected nodes, enterprise software aesthetic, deep blue with golden highlights, clean lines --style art
```

### Supporting Graphics

```
# Dashboard mockup background
/firefly-generate Clean desk workspace from above, minimal objects, soft shadows, warm neutral tones, professional photography --style photo

# Team collaboration illustration
/firefly-generate Abstract representation of collaboration, connected circles, warm corporate colors, flat illustration style --style art
```

## Complete Integration Example

```html
<!-- Generated with bencium-innovative-ux-designer + Adobe Firefly -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FlowBoard - Elegant Project Management</title>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600&family=Source+Sans+3:wght@300;400;600&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      theme: {
        extend: {
          colors: {
            'navy': '#1a2332',
            'gold': '#c9a962',
            'cream': '#f8f6f2',
          },
          fontFamily: {
            'display': ['Playfair Display', 'serif'],
            'body': ['Source Sans 3', 'sans-serif'],
          }
        }
      }
    }
  </script>
</head>
<body class="bg-cream font-body">
  <!-- Hero Section with Firefly-generated background -->
  <section class="relative min-h-screen flex items-center overflow-hidden">
    <!-- Background: Use Firefly-generated abstract art -->
    <div class="absolute inset-0">
      <img
        src="[FIREFLY_GENERATED_HERO_IMAGE]"
        alt=""
        class="w-full h-full object-cover opacity-20"
      />
      <div class="absolute inset-0 bg-gradient-to-br from-navy/90 to-navy/70"></div>
    </div>

    <!-- Content -->
    <div class="relative z-10 max-w-6xl mx-auto px-8 py-24">
      <nav class="flex justify-between items-center mb-24">
        <span class="font-display text-2xl text-cream">FlowBoard</span>
        <div class="flex gap-8 text-cream/80">
          <a href="#features" class="hover:text-gold transition-colors">Features</a>
          <a href="#pricing" class="hover:text-gold transition-colors">Pricing</a>
          <a href="#" class="px-6 py-2 border border-gold text-gold hover:bg-gold hover:text-navy transition-all">
            Get Started
          </a>
        </div>
      </nav>

      <div class="max-w-2xl">
        <h1 class="font-display text-6xl text-cream leading-tight mb-6">
          Project management, <span class="text-gold">refined.</span>
        </h1>
        <p class="text-xl text-cream/70 leading-relaxed mb-12">
          A thoughtfully designed workspace for teams who value clarity,
          simplicity, and the art of getting things done beautifully.
        </p>
        <div class="flex gap-4">
          <button class="px-8 py-4 bg-gold text-navy font-semibold hover:bg-gold/90 transition-colors">
            Start Free Trial
          </button>
          <button class="px-8 py-4 border border-cream/30 text-cream hover:border-cream/60 transition-colors">
            Watch Demo
          </button>
        </div>
      </div>
    </div>
  </section>

  <!-- Features with Firefly-generated icons -->
  <section id="features" class="py-24 bg-white">
    <div class="max-w-6xl mx-auto px-8">
      <h2 class="font-display text-4xl text-navy text-center mb-16">
        Crafted for focus
      </h2>
      <div class="grid md:grid-cols-3 gap-12">
        <!-- Feature cards with Firefly-generated icons -->
        <div class="text-center">
          <div class="w-20 h-20 mx-auto mb-6 rounded-full bg-cream flex items-center justify-center">
            <img src="[FIREFLY_ICON_BOARDS]" alt="" class="w-10 h-10" />
          </div>
          <h3 class="font-display text-xl text-navy mb-3">Intuitive Boards</h3>
          <p class="text-navy/60">Visualize your workflow with elegant kanban boards designed for clarity.</p>
        </div>
        <div class="text-center">
          <div class="w-20 h-20 mx-auto mb-6 rounded-full bg-cream flex items-center justify-center">
            <img src="[FIREFLY_ICON_TIMELINE]" alt="" class="w-10 h-10" />
          </div>
          <h3 class="font-display text-xl text-navy mb-3">Timeline View</h3>
          <p class="text-navy/60">See your projects unfold with a refined timeline that respects your time.</p>
        </div>
        <div class="text-center">
          <div class="w-20 h-20 mx-auto mb-6 rounded-full bg-cream flex items-center justify-center">
            <img src="[FIREFLY_ICON_TEAM]" alt="" class="w-10 h-10" />
          </div>
          <h3 class="font-display text-xl text-navy mb-3">Team Harmony</h3>
          <p class="text-navy/60">Collaborate seamlessly with tools that bring your team together.</p>
        </div>
      </div>
    </div>
  </section>
</body>
</html>
```

## Tips for Best Results

1. **Match the aesthetic**: When generating Firefly images, use language that matches your chosen bencium aesthetic tone (luxury/refined, brutally minimal, etc.)

2. **Color consistency**: Include specific color references in your Firefly prompts that match your design palette

3. **Style coherence**: Use `--style art` for illustrations and UI elements, `--style photo` for realistic imagery

4. **Generate variations**: Always generate 2-4 variations to pick the best fit

5. **Background removal**: Use `/firefly-edit remove-bg` for product images that need to be composited

## Firefly Prompt Templates for This Design

```
# For luxury/refined aesthetic:
"[subject], deep navy and champagne gold palette, elegant, premium, refined, subtle sophistication"

# For minimalist aesthetic:
"[subject], stark contrast, generous whitespace, single accent color, clean lines"

# For editorial aesthetic:
"[subject], magazine quality, dramatic lighting, strong typography placement area"
```
