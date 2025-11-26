---
name: firefly-prompts
description: "Expert prompt engineering skill for Adobe Firefly. Use to craft effective prompts for image generation."
---

# Adobe Firefly Prompt Engineering Skill

This skill provides expertise in crafting effective prompts for Adobe Firefly image generation.

## Prompt Structure

### Basic Formula
```
[Subject] + [Description] + [Environment] + [Lighting] + [Style] + [Mood]
```

### Example Breakdown
```
"A golden retriever puppy (subject) playing with a red ball (description)
in a sunny park (environment) with soft afternoon light (lighting)
in the style of professional pet photography (style)
conveying joy and playfulness (mood)"
```

## Key Elements

### Subject Definition
- Be specific about the main subject
- Include relevant details (age, color, size)
- Specify quantity if multiple subjects

**Good:** "A vintage red 1967 Ford Mustang convertible"
**Weak:** "A car"

### Composition & Framing
- Camera angle: eye-level, bird's eye, worm's eye
- Shot type: close-up, medium, wide, extreme close-up
- Framing: centered, rule of thirds, leading lines

**Example:** "Close-up portrait from a slight low angle"

### Lighting
- Type: natural, studio, dramatic, soft
- Direction: front, back, side, rim
- Quality: harsh, diffused, golden hour

**Examples:**
- "Dramatic side lighting with deep shadows"
- "Soft diffused natural light from a window"
- "Golden hour backlighting with lens flare"

### Style References
- Artistic movements: impressionist, art deco, minimalist
- Photography styles: portrait, landscape, macro
- Specific artists (when appropriate)

**Examples:**
- "In the style of vintage travel posters"
- "Minimalist Scandinavian design aesthetic"
- "Cinematic color grading like a Wes Anderson film"

### Mood & Atmosphere
- Emotional tone: serene, energetic, mysterious
- Atmosphere: foggy, clear, stormy
- Color mood: warm, cool, vibrant, muted

## Content Classes

### Photo (`contentClass: "photo"`)
Best prompts include:
- Camera/lens specifications
- Realistic lighting descriptions
- Technical photography terms
- Real-world references

**Example:**
```
"Professional product photography of a luxury watch on black velvet,
shot with a macro lens, soft studio lighting with subtle reflections,
8K detail, commercial advertising style"
```

### Art (`contentClass: "art"`)
Best prompts include:
- Artistic style references
- Medium specifications (oil paint, watercolor, digital)
- Artistic techniques
- Abstract concepts

**Example:**
```
"Watercolor painting of a Japanese garden in spring,
loose brushstrokes, soft bleeding colors,
traditional ukiyo-e influence, peaceful and contemplative mood"
```

## Negative Prompts

Use to exclude unwanted elements:
- "blurry, low quality, distorted"
- "text, watermark, signature"
- "extra limbs, deformed"
- Specific unwanted elements

## Prompt Templates

### Product Photography
```
"Professional product photography of [PRODUCT],
[SURFACE/BACKGROUND], [LIGHTING SETUP],
[ANGLE], commercial advertising quality, 8K detail"
```

### Portrait
```
"[SHOT TYPE] portrait of [SUBJECT DESCRIPTION],
[EXPRESSION/POSE], [LIGHTING], [BACKGROUND],
[STYLE], [MOOD]"
```

### Landscape
```
"[LOCATION TYPE] landscape, [TIME OF DAY],
[WEATHER/ATMOSPHERE], [FOREGROUND ELEMENTS],
[STYLE], [MOOD]"
```

### Concept Art
```
"Concept art of [SUBJECT], [SETTING],
[ART STYLE], [COLOR PALETTE],
detailed illustration, professional quality"
```

## Iteration Strategy

1. **Start broad**: General concept to establish direction
2. **Add specificity**: Details that matter most
3. **Refine style**: Artistic direction and mood
4. **Adjust parameters**: Size, variations, content class
5. **Use variations**: Generate multiple, pick best
6. **Iterate**: Refine based on results
