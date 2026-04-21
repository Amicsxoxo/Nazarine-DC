# Design System Specification: The Nazarine DC

## 1. Overview & Creative North Star

### Creative North Star: "The Nazarine DC"
This design system moves beyond the utility of a standard dashboard to create a high-end editorial experience that feels like a premium sustainability journal. The "Nazarine DC" represents the intersection of raw ecological power (Forest Greens) and precise technological monitoring (Sky Blues). 

To achieve a signature look, we reject the rigid, "boxed-in" layout of traditional SaaS. Instead, we utilize **Intentional Asymmetry** and **Organic Layering**. Data visualizations should bleed off the edges of containers, and typography should be used as a structural element. By overlapping high-contrast typography with soft, translucent surfaces, we create a sense of depth and environmental stewardship that feels both professional and visionary.

---

## 2. Colors & Tonal Logic

The palette is rooted in deep, authoritative greens, balanced by the airy clarity of sky blues and the cleanliness of mint accents.

### The "No-Line" Rule
**Explicit Instruction:** Designers are prohibited from using 1px solid borders to define sections or containers. Boundaries must be defined through:
1.  **Background Color Shifts:** Placing a `surface_container_lowest` (#ffffff) card against a `surface_container_low` (#f2f4f6) section.
2.  **Tonal Transitions:** Using subtle value changes in the surface-container tiers to create perceived edges.

### Surface Hierarchy & Nesting
Treat the UI as a physical stack of fine materials.
*   **Base:** `background` (#f7f9fb) serves as the canvas.
*   **Primary Sections:** Use `surface_container_low` (#f2f4f6) to group related data.
*   **Elevated Modules:** Use `surface_container_lowest` (#ffffff) for individual cards or interactive modules to create a "soft lift."
*   **Actionable Elements:** Use `primary_container` (#1b4332) for high-emphasis containers that need to command attention.

### The "Glass & Gradient" Rule
To elevate the dashboard from "standard" to "custom," use **Glassmorphism** for floating overlays (e.g., tooltips, filter drawers). Apply a 60% opacity to `surface_container_lowest` with a `backdrop-blur: 20px`. 
**Signature Textures:** For primary data trends or Hero CTAs, use a subtle linear gradient from `primary` (#012d1d) to `primary_container` (#1b4332) at a 135-degree angle. This provides a "visual soul" that flat colors lack.

---

## 3. Typography

The typographic system utilizes a dual-personality approach: **Manrope** for editorial impact and **Public Sans/Inter** for technical precision.

*   **Display & Headlines (Manrope):** These are your "vocal" elements. Use `display-lg` and `headline-lg` with tight letter-spacing (-0.02em) to create an authoritative, editorial feel. 
*   **Titles & Body (Public Sans):** Chosen for its high x-height and readability. `title-lg` should be used for data card headers to ensure clarity.
*   **Labels (Inter):** Reserved for metadata and micro-copy. `label-sm` should be used in all-caps with +0.05em letter spacing for a "technical instrumentation" look.

---

## 4. Elevation & Depth

We convey hierarchy through **Tonal Layering** rather than traditional structural shadows.

### The Layering Principle
Depth is achieved by stacking surface-container tiers. Placing a `surface_container_highest` (#e0e3e5) element inside a `surface_container` (#eceef0) creates a natural "inset" feel, perfect for search bars or data input areas.

### Ambient Shadows
When a component must "float" (e.g., a modal or a primary FAB):
*   **Blur:** 40px to 60px.
*   **Opacity:** 4% to 8%.
*   **Color:** Use a tinted version of `on_surface` (#191c1e) to ensure the shadow feels like a natural obstruction of light, not a grey smudge.

### The "Ghost Border" Fallback
If accessibility requirements demand a border, use a **Ghost Border**: `outline_variant` (#c1c8c2) at 15% opacity. It should be felt, not seen.

---

## 5. Components

### Buttons
*   **Primary:** Background: `primary` (#012d1d); Text: `on_primary` (#ffffff). Shape: `md` (0.375rem).
*   **Secondary:** Background: `secondary_container` (#a0f4c8); Text: `on_secondary_container` (#19724f).
*   **Tertiary:** No background. Text: `primary` (#012d1d) with `label-md` styling.

### Chips (Data Tags)
Use `full` (9999px) roundedness. 
*   **Eco-Status Chips:** Use `secondary_fixed` (#a0f4c8) for "Healthy" statuses and `tertiary_fixed` (#c9e6ff) for "Optimizing."

### Cards & Lists
**Strict Rule:** No divider lines. Separate list items using the Spacing Scale (e.g., 12px vertical gap) or by alternating background tints between `surface_container_low` and `surface_container`. 

### Luminous Data Viz (Custom Component)
Energy charts should not use standard thin lines. Use a 3px stroke width with a `surface_tint` (#3f6653) glow effect. Area charts should use a gradient transition from `tertiary_fixed_dim` (#89ceff) at the top to 0% opacity at the baseline.

### Input Fields
Background: `surface_container_highest` (#e0e3e5). 
Active State: A 2px bottom-border only, using `primary` (#012d1d). This mimics high-end stationary and feels less "boxy" than a four-sided focus ring.

---

## 6. Do's and Don'ts

### Do
*   **Do** use expansive white space. A clean energy dashboard should feel "breathable."
*   **Do** align large Display typography to the left, allowing data points to sit asymmetrically to the right.
*   **Do** use `tertiary` (#00293e) for "Power" or "Grid" related data to provide a cooling contrast to the green palette.

### Don't
*   **Don't** use pure black (#000000). Always use `on_background` (#191c1e) for text to maintain a sophisticated, soft-contrast look.
*   **Don't** use the `xl` (0.75rem) roundedness on primary cards; keep them at `lg` (0.5rem) to maintain a professional, architectural structure.
*   **Don't** use standard "Success Green" (#00FF00). Only use the specified `secondary` (#0e6c4a) or `secondary_fixed` (#a0f4c8) to keep the aesthetic premium and curated.