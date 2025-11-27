# Example 4: Analytics Dashboard with AI Illustrations

This example demonstrates combining `bencium-controlled-ux-designer` with Adobe Firefly for a data-focused dashboard application with custom illustrations.

## Workflow

### Step 1: Design the Dashboard Structure

Use bencium-controlled-ux-designer for systematic design:

```
Create an analytics dashboard for a fitness tracking app called "PulseMetrics".
Requirements:
- Clear data visualization hierarchy
- Accessible color system for charts
- Consistent spacing and component patterns
- Dark mode by default for reduced eye strain
```

### Step 2: Generate Custom Illustrations

Use Adobe Firefly to create empty state illustrations and decorative elements:

```
# Empty state illustration
/firefly-generate Minimalist illustration of person meditating with data points floating around, soft blue and purple palette, flat design, peaceful --style art --size 800x600

# Achievement badges
/firefly-workflow art-series --theme "fitness achievement icons" --style "flat vector illustration" --count 8
```

## Dashboard UI Elements + Firefly Assets

### Empty States

Empty states are prime opportunities for Firefly illustrations:

```
# No data yet
/firefly-generate Person looking at empty chart with optimistic expression, minimalist illustration, muted colors, friendly --style art

# Search no results
/firefly-generate Magnifying glass looking at empty space, cute illustration, soft shadows, pastel colors --style art

# Connection lost
/firefly-generate Unplugged cable with sad face, simple illustration, monochrome with accent color --style art

# First-time user
/firefly-generate Person taking first steps on journey, abstract path ahead, encouraging illustration --style art
```

### Feature Illustrations

```
# Goal tracking feature
/firefly-generate Abstract representation of progress and achievement, mountain peak with flag, modern illustration --style art

# Social features
/firefly-generate Connected circles representing community, warm colors, friendly illustration --style art

# Analytics feature
/firefly-generate Abstract data visualization art, flowing charts and graphs, aesthetic data representation --style art
```

### Achievement Badges

```
/firefly-generate Fitness achievement badge icon, running figure, gold medal style, flat design vector --style art --size 256x256 --variations 4

/firefly-generate Step goal achievement badge, footprints icon, celebratory design, app icon style --style art --size 256x256

/firefly-generate Streak achievement badge, flame icon, premium look, game achievement style --style art --size 256x256
```

## Complete Dashboard Example

```html
<!-- Generated with bencium-controlled-ux-designer + Adobe Firefly -->
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PulseMetrics - Dashboard</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            // Accessible dark mode palette
            'surface-0': '#0F0F12',
            'surface-1': '#1A1A1F',
            'surface-2': '#252529',
            'surface-3': '#303035',
            'text-primary': '#FAFAFA',
            'text-secondary': '#A0A0A8',
            'text-muted': '#606068',
            // Accessible chart colors (distinguishable for colorblind users)
            'chart-1': '#6366F1', // Indigo
            'chart-2': '#22D3EE', // Cyan
            'chart-3': '#F472B6', // Pink
            'chart-4': '#FBBF24', // Amber
            'chart-5': '#34D399', // Emerald
            'accent': '#6366F1',
            'accent-hover': '#4F46E5',
            'success': '#22C55E',
            'warning': '#F59E0B',
            'error': '#EF4444',
          }
        }
      }
    }
  </script>
  <style>
    /* Smooth scrollbar for dark mode */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #1A1A1F; }
    ::-webkit-scrollbar-thumb { background: #404048; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #505058; }
  </style>
</head>
<body class="bg-surface-0 text-text-primary min-h-screen">
  <div class="flex">

    <!-- Sidebar -->
    <aside class="w-64 bg-surface-1 min-h-screen p-4 flex flex-col">
      <div class="flex items-center gap-3 px-2 mb-8">
        <!-- Logo could be Firefly-generated -->
        <div class="w-10 h-10 bg-accent rounded-lg flex items-center justify-center">
          <img src="[FIREFLY_LOGO_ICON]" alt="" class="w-6 h-6" />
        </div>
        <span class="font-semibold text-lg">PulseMetrics</span>
      </div>

      <nav class="flex-1 space-y-1">
        <a href="#" class="flex items-center gap-3 px-3 py-2 rounded-lg bg-accent/10 text-accent">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6z"></path>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6z"></path>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2z"></path>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"></path>
          </svg>
          Dashboard
        </a>
        <a href="#" class="flex items-center gap-3 px-3 py-2 rounded-lg text-text-secondary hover:bg-surface-2 transition-colors">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
          </svg>
          Analytics
        </a>
        <a href="#" class="flex items-center gap-3 px-3 py-2 rounded-lg text-text-secondary hover:bg-surface-2 transition-colors">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          Activity
        </a>
        <a href="#" class="flex items-center gap-3 px-3 py-2 rounded-lg text-text-secondary hover:bg-surface-2 transition-colors">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"></path>
          </svg>
          Achievements
        </a>
      </nav>

      <!-- User profile -->
      <div class="pt-4 border-t border-surface-3">
        <div class="flex items-center gap-3 px-2">
          <img
            src="[FIREFLY_AVATAR_BG]"
            alt="User avatar"
            class="w-10 h-10 rounded-full object-cover"
          />
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium truncate">Alex Johnson</p>
            <p class="text-xs text-text-muted truncate">Premium Plan</p>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 p-8">
      <!-- Header -->
      <header class="flex items-center justify-between mb-8">
        <div>
          <h1 class="text-2xl font-bold">Good morning, Alex</h1>
          <p class="text-text-secondary">Here's your fitness overview for today</p>
        </div>
        <div class="flex items-center gap-4">
          <button class="p-2 rounded-lg hover:bg-surface-2 transition-colors text-text-secondary">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path>
            </svg>
          </button>
        </div>
      </header>

      <!-- Stats Grid -->
      <div class="grid grid-cols-4 gap-6 mb-8">
        <div class="bg-surface-1 rounded-xl p-6">
          <div class="flex items-center justify-between mb-4">
            <span class="text-text-secondary text-sm">Steps Today</span>
            <span class="text-success text-xs">+12%</span>
          </div>
          <p class="text-3xl font-bold">8,432</p>
          <div class="mt-4 h-2 bg-surface-3 rounded-full overflow-hidden">
            <div class="h-full bg-chart-1 rounded-full" style="width: 84%"></div>
          </div>
          <p class="text-xs text-text-muted mt-2">84% of 10,000 goal</p>
        </div>

        <div class="bg-surface-1 rounded-xl p-6">
          <div class="flex items-center justify-between mb-4">
            <span class="text-text-secondary text-sm">Calories Burned</span>
            <span class="text-success text-xs">+8%</span>
          </div>
          <p class="text-3xl font-bold">1,842</p>
          <div class="mt-4 h-2 bg-surface-3 rounded-full overflow-hidden">
            <div class="h-full bg-chart-3 rounded-full" style="width: 92%"></div>
          </div>
          <p class="text-xs text-text-muted mt-2">92% of 2,000 goal</p>
        </div>

        <div class="bg-surface-1 rounded-xl p-6">
          <div class="flex items-center justify-between mb-4">
            <span class="text-text-secondary text-sm">Active Minutes</span>
            <span class="text-warning text-xs">-3%</span>
          </div>
          <p class="text-3xl font-bold">47</p>
          <div class="mt-4 h-2 bg-surface-3 rounded-full overflow-hidden">
            <div class="h-full bg-chart-2 rounded-full" style="width: 78%"></div>
          </div>
          <p class="text-xs text-text-muted mt-2">78% of 60 min goal</p>
        </div>

        <div class="bg-surface-1 rounded-xl p-6">
          <div class="flex items-center justify-between mb-4">
            <span class="text-text-secondary text-sm">Sleep Score</span>
            <span class="text-success text-xs">+5%</span>
          </div>
          <p class="text-3xl font-bold">86</p>
          <div class="mt-4 h-2 bg-surface-3 rounded-full overflow-hidden">
            <div class="h-full bg-chart-5 rounded-full" style="width: 86%"></div>
          </div>
          <p class="text-xs text-text-muted mt-2">7h 23m last night</p>
        </div>
      </div>

      <!-- Charts and Activity -->
      <div class="grid grid-cols-3 gap-6 mb-8">
        <!-- Weekly Activity Chart -->
        <div class="col-span-2 bg-surface-1 rounded-xl p-6">
          <div class="flex items-center justify-between mb-6">
            <h2 class="font-semibold">Weekly Activity</h2>
            <select class="bg-surface-2 text-text-secondary text-sm rounded-lg px-3 py-1.5 border-none focus:ring-2 focus:ring-accent">
              <option>This Week</option>
              <option>Last Week</option>
              <option>Last Month</option>
            </select>
          </div>
          <!-- Chart placeholder - would use Chart.js or similar -->
          <div class="h-64 flex items-end justify-between gap-2">
            <div class="flex-1 flex flex-col items-center gap-2">
              <div class="w-full bg-chart-1 rounded-t" style="height: 60%"></div>
              <span class="text-xs text-text-muted">Mon</span>
            </div>
            <div class="flex-1 flex flex-col items-center gap-2">
              <div class="w-full bg-chart-1 rounded-t" style="height: 80%"></div>
              <span class="text-xs text-text-muted">Tue</span>
            </div>
            <div class="flex-1 flex flex-col items-center gap-2">
              <div class="w-full bg-chart-1 rounded-t" style="height: 45%"></div>
              <span class="text-xs text-text-muted">Wed</span>
            </div>
            <div class="flex-1 flex flex-col items-center gap-2">
              <div class="w-full bg-chart-1 rounded-t" style="height: 90%"></div>
              <span class="text-xs text-text-muted">Thu</span>
            </div>
            <div class="flex-1 flex flex-col items-center gap-2">
              <div class="w-full bg-chart-1 rounded-t" style="height: 70%"></div>
              <span class="text-xs text-text-muted">Fri</span>
            </div>
            <div class="flex-1 flex flex-col items-center gap-2">
              <div class="w-full bg-chart-1 rounded-t" style="height: 55%"></div>
              <span class="text-xs text-text-muted">Sat</span>
            </div>
            <div class="flex-1 flex flex-col items-center gap-2">
              <div class="w-full bg-accent/30 border-2 border-dashed border-accent rounded-t" style="height: 84%"></div>
              <span class="text-xs text-accent">Today</span>
            </div>
          </div>
        </div>

        <!-- Achievements Panel with Firefly badges -->
        <div class="bg-surface-1 rounded-xl p-6">
          <h2 class="font-semibold mb-6">Recent Achievements</h2>
          <div class="space-y-4">
            <div class="flex items-center gap-4 p-3 bg-surface-2 rounded-lg">
              <img src="[FIREFLY_BADGE_STREAK]" alt="" class="w-12 h-12" />
              <div>
                <p class="font-medium">7 Day Streak</p>
                <p class="text-xs text-text-muted">Earned yesterday</p>
              </div>
            </div>
            <div class="flex items-center gap-4 p-3 bg-surface-2 rounded-lg">
              <img src="[FIREFLY_BADGE_STEPS]" alt="" class="w-12 h-12" />
              <div>
                <p class="font-medium">10K Steps Club</p>
                <p class="text-xs text-text-muted">Earned 3 days ago</p>
              </div>
            </div>
            <div class="flex items-center gap-4 p-3 bg-surface-2 rounded-lg">
              <img src="[FIREFLY_BADGE_EARLY]" alt="" class="w-12 h-12" />
              <div>
                <p class="font-medium">Early Bird</p>
                <p class="text-xs text-text-muted">Earned last week</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State Example -->
      <div class="bg-surface-1 rounded-xl p-8">
        <div class="text-center max-w-md mx-auto">
          <!-- Firefly illustration for empty state -->
          <img
            src="[FIREFLY_EMPTY_STATE]"
            alt="No workout data yet"
            class="w-48 h-48 mx-auto mb-6 opacity-80"
          />
          <h3 class="text-xl font-semibold mb-2">No workouts logged today</h3>
          <p class="text-text-secondary mb-6">
            Start tracking your first workout to see your progress here.
          </p>
          <button class="px-6 py-3 bg-accent hover:bg-accent-hover text-white rounded-lg transition-colors">
            Log Workout
          </button>
        </div>
      </div>

    </main>
  </div>
</body>
</html>
```

## Firefly Prompts for Dashboard Elements

### Onboarding Illustrations

```
# Welcome screen
/firefly-generate Happy person starting fitness journey, abstract path ahead, sunrise colors, motivational illustration --style art

# Setup profile
/firefly-generate Person customizing their avatar, floating UI elements around them, friendly illustration --style art

# Connect device
/firefly-generate Smartwatch connecting to app, wireless signal visualization, tech illustration --style art

# Set goals
/firefly-generate Target with arrow, mountains in background representing goals, achievement illustration --style art
```

### Status Illustrations

```
# Loading state
/firefly-generate Abstract loading animation frame, circular progress, smooth gradients --style art

# Success state
/firefly-generate Celebration confetti, checkmark, achievement moment, happy colors --style art

# Error state
/firefly-generate Gentle error illustration, puzzle piece that doesn't fit, soft colors not alarming --style art

# Maintenance
/firefly-generate Friendly robot doing maintenance, tools and gears, calm illustration --style art
```

### Background Patterns

```
# Subtle dashboard background
/firefly-generate Subtle geometric pattern, very low contrast, dark background with slightly lighter shapes, minimal --style art

# Card texture
/firefly-generate Subtle noise texture, grain overlay, dark mode friendly, barely visible --style art
```

## Accessibility for Dashboard + Firefly Images

1. **Decorative images**: Use `alt=""` for illustrations that don't convey information
2. **Meaningful images**: Provide descriptive alt text for badges and achievements
3. **Color contrast**: Ensure chart colors meet 3:1 contrast for graphical elements
4. **Don't rely on color**: Add patterns or labels to differentiate data series
5. **Reduced motion**: Provide static alternatives for any animated Firefly content
