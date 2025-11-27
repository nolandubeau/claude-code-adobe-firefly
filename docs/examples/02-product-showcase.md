# Example 2: E-Commerce Product Showcase

This example demonstrates combining `bencium-controlled-ux-designer` with Adobe Firefly's product photography pipeline for accessible, production-ready e-commerce pages.

## Workflow

### Step 1: Design Accessible Product Page

Use the bencium-controlled-ux-designer skill for WCAG AA compliant design:

```
Create a product detail page for a premium headphones e-commerce site.
Requirements:
- WCAG 2.1 AA compliance
- Clear visual hierarchy
- Mobile-first responsive design
- Accessible color contrast
```

### Step 2: Product Photography Pipeline

Use the Firefly workflow agent for professional product shots:

```
/firefly-workflow product-shot --product "premium wireless headphones" --background "clean gradient studio lighting"
```

### Step 3: Generate Lifestyle Context Images

```
/firefly-generate Person wearing headphones while working at modern desk, soft natural lighting, lifestyle photography, warm tones --style photo --size 1200x800
```

## Complete Firefly Product Pipeline

### 1. Remove Background from Product Photo

```bash
# If you have an existing product photo
/firefly-edit remove-bg https://example.com/headphones-raw.jpg
```

### 2. Generate Custom Background

```
/firefly-generate Soft gradient studio backdrop, subtle warm to cool transition, product photography lighting setup, clean minimal --style photo --size 2000x2000
```

### 3. Composite with Generative Fill

```
/firefly-edit fill [composite-image-url] --mask [product-area-mask] --prompt "Premium headphones product photography, studio lighting"
```

### 4. Create Size Variations

```
/firefly-edit expand [product-shot-url] --size 1920x1080 --prompt "Continue the studio backdrop seamlessly"
```

## Sample Prompts for Product Categories

### Tech Products

```
/firefly-generate Premium wireless headphones floating on clean white background, soft shadows, product photography, studio lighting --style photo

/firefly-generate Minimalist smartphone mockup on marble surface, natural lighting, luxury tech aesthetic --style photo
```

### Fashion Items

```
/firefly-generate Leather watch on textured concrete surface, dramatic side lighting, editorial product photography --style photo

/firefly-generate Designer handbag on neutral linen backdrop, soft window light, fashion photography --style photo
```

### Home Goods

```
/firefly-generate Modern ceramic vase with dried flowers on wooden shelf, warm afternoon light, lifestyle product photography --style photo

/firefly-generate Luxury candle in amber glass, cozy living room setting, hygge aesthetic, soft focus background --style photo
```

## Accessible Design Integration

```html
<!-- Generated with bencium-controlled-ux-designer + Adobe Firefly -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AuraSound Pro - Premium Wireless Headphones</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      theme: {
        extend: {
          colors: {
            // WCAG AA compliant color system
            'surface': '#FAFAFA',
            'surface-elevated': '#FFFFFF',
            'text-primary': '#1A1A1A',    // 15.3:1 contrast
            'text-secondary': '#525252',  // 7.1:1 contrast
            'accent': '#2563EB',          // 4.6:1 on white
            'accent-dark': '#1D4ED8',     // 5.9:1 on white
          }
        }
      }
    }
  </script>
</head>
<body class="bg-surface text-text-primary">
  <!-- Skip link for accessibility -->
  <a href="#main-content" class="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-accent text-white px-4 py-2 z-50">
    Skip to main content
  </a>

  <main id="main-content" class="max-w-7xl mx-auto px-4 py-8">
    <nav aria-label="Breadcrumb" class="mb-8">
      <ol class="flex gap-2 text-sm text-text-secondary">
        <li><a href="/" class="hover:text-accent focus:outline-none focus:ring-2 focus:ring-accent rounded">Home</a></li>
        <li aria-hidden="true">/</li>
        <li><a href="/audio" class="hover:text-accent focus:outline-none focus:ring-2 focus:ring-accent rounded">Audio</a></li>
        <li aria-hidden="true">/</li>
        <li aria-current="page" class="text-text-primary">AuraSound Pro</li>
      </ol>
    </nav>

    <div class="grid lg:grid-cols-2 gap-12">
      <!-- Product Images - Firefly Generated -->
      <section aria-label="Product images">
        <div class="bg-surface-elevated rounded-lg overflow-hidden mb-4">
          <!-- Main product image from Firefly product pipeline -->
          <img
            src="[FIREFLY_PRODUCT_MAIN]"
            alt="AuraSound Pro wireless headphones in matte black finish, front view showing premium cushioned ear cups and adjustable headband"
            class="w-full aspect-square object-contain"
          />
        </div>

        <!-- Thumbnail gallery -->
        <div class="grid grid-cols-4 gap-4" role="group" aria-label="Additional product views">
          <button
            class="bg-surface-elevated rounded-lg p-2 border-2 border-accent focus:outline-none focus:ring-2 focus:ring-accent"
            aria-pressed="true"
            aria-label="Front view, currently selected"
          >
            <img src="[FIREFLY_THUMB_1]" alt="" class="w-full aspect-square object-contain" />
          </button>
          <button
            class="bg-surface-elevated rounded-lg p-2 border-2 border-transparent hover:border-accent/50 focus:outline-none focus:ring-2 focus:ring-accent"
            aria-pressed="false"
            aria-label="Side view"
          >
            <img src="[FIREFLY_THUMB_2]" alt="" class="w-full aspect-square object-contain" />
          </button>
          <button
            class="bg-surface-elevated rounded-lg p-2 border-2 border-transparent hover:border-accent/50 focus:outline-none focus:ring-2 focus:ring-accent"
            aria-pressed="false"
            aria-label="Lifestyle shot"
          >
            <!-- Firefly lifestyle image -->
            <img src="[FIREFLY_LIFESTYLE]" alt="" class="w-full aspect-square object-cover" />
          </button>
          <button
            class="bg-surface-elevated rounded-lg p-2 border-2 border-transparent hover:border-accent/50 focus:outline-none focus:ring-2 focus:ring-accent"
            aria-pressed="false"
            aria-label="Detail view of ear cushion"
          >
            <img src="[FIREFLY_THUMB_4]" alt="" class="w-full aspect-square object-contain" />
          </button>
        </div>
      </section>

      <!-- Product Details -->
      <section aria-labelledby="product-title">
        <h1 id="product-title" class="text-3xl font-bold mb-2">AuraSound Pro</h1>
        <p class="text-text-secondary mb-4">Premium Wireless Headphones</p>

        <!-- Price with proper formatting for screen readers -->
        <p class="text-2xl font-semibold mb-6">
          <span class="sr-only">Price:</span>
          <span aria-label="349 dollars">$349</span>
        </p>

        <!-- Color selection with accessible controls -->
        <fieldset class="mb-6">
          <legend class="text-sm font-medium mb-3">Color</legend>
          <div class="flex gap-3" role="radiogroup">
            <label class="relative cursor-pointer">
              <input type="radio" name="color" value="black" class="sr-only peer" checked />
              <span
                class="block w-10 h-10 rounded-full bg-gray-900 ring-2 ring-offset-2 ring-transparent peer-checked:ring-accent peer-focus:ring-accent"
                aria-label="Matte Black"
              ></span>
            </label>
            <label class="relative cursor-pointer">
              <input type="radio" name="color" value="silver" class="sr-only peer" />
              <span
                class="block w-10 h-10 rounded-full bg-gray-300 ring-2 ring-offset-2 ring-transparent peer-checked:ring-accent peer-focus:ring-accent"
                aria-label="Silver"
              ></span>
            </label>
            <label class="relative cursor-pointer">
              <input type="radio" name="color" value="navy" class="sr-only peer" />
              <span
                class="block w-10 h-10 rounded-full bg-blue-900 ring-2 ring-offset-2 ring-transparent peer-checked:ring-accent peer-focus:ring-accent"
                aria-label="Navy Blue"
              ></span>
            </label>
          </div>
        </fieldset>

        <!-- Add to cart with clear feedback -->
        <button
          class="w-full bg-accent hover:bg-accent-dark text-white font-semibold py-4 px-8 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2"
        >
          Add to Cart
        </button>

        <!-- Product description -->
        <div class="mt-8 prose prose-slate">
          <h2 class="text-lg font-semibold mb-3">About this product</h2>
          <p class="text-text-secondary leading-relaxed">
            Experience premium audio with AuraSound Pro. Featuring 40mm custom drivers,
            active noise cancellation, and up to 30 hours of battery life. The memory foam
            ear cushions provide all-day comfort for extended listening sessions.
          </p>
        </div>
      </section>
    </div>
  </main>
</body>
</html>
```

## Accessibility Considerations

When integrating Firefly images with accessible designs:

1. **Alt text**: Always provide descriptive alt text for product images
2. **Color independence**: Don't rely solely on Firefly-generated color variations to convey information
3. **Contrast**: Ensure text overlaid on Firefly images meets WCAG contrast requirements
4. **Loading states**: Provide skeleton screens while Firefly images load
5. **Image format**: Use appropriate formats (WebP with JPEG fallback) for performance

## Firefly Best Practices for E-Commerce

1. **Consistent lighting**: Use similar prompts for lighting across product line
2. **Background removal**: Always remove backgrounds for composite flexibility
3. **Multiple angles**: Generate 4+ angles for comprehensive product views
4. **Lifestyle context**: Include at least one lifestyle/context shot
5. **Detail shots**: Generate close-ups for material and feature highlights
