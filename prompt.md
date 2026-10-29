# TASK: Refactor & Elevate Lantern into a High-End Interactive Scientific Explainer & Dashboard Compiler

## 1. Context & Architectural Mission

`Lantern` is the interactive counterpart to `Snowpack` within the **Frost** ecosystem. Where `Snowpack` compiles static, publication-grade PDFs (reports, IEEE papers, Keynote slide decks via Typst/LaTeX), `Lantern` compiles and serves **dynamic, interactive web explainers and simulation dashboards** (DOM, HTML5 Canvases, live parameter sliders, KaTeX math, and Plotly embeds).

### The Current State & Problem
The initial build of `Lantern` established a great core:
- A pure-Python + Nix compilation engine (`compiler.py`).
- An integrated SSE live-reloading dev server (`server.py`) that watches Markdown and Python scripts.
- Offline-bundled KaTeX for instant math typesetting.
- A functional `::: plot` directive that bridges to `Barograph`.
- An 800+ line dark-mode design system in `lantern.css`.

**The Architectural Bug:** The initial directives hardcoded domain-specific optimization algorithms (`walker.py` with Rosenbrock valley and BFGS, `barrier.py` with logarithmic penalty walls, `decision.py`) directly into `src/lantern/directives/`.

`Lantern` must be a **general-purpose scientific compiler** for any discipline (robotics, signal processing, control theory, machine learning, physics, biology, finance). We want to turn `Lantern` into a complete, professional design system and compiler that eliminates token waste when authoring explainers.

---

## 2. The Three Component Families Target Architecture

```text
src/lantern/
├── __init__.py
├── __main__.py
├── cli.py                     # CLI commands (build, serve, new, list)
├── compiler.py                # Markdown + Jinja2 orchestrator
├── directives/                # Markdown Block Processors (::: syntax)
│   ├── __init__.py
│   │
│   ├── # 📐 FAMILY 1: LAYOUT & SPATIAL CHROME (Strips, Grids & Navigation)
│   │   ├── grid.py            # ::: grid [50/50 | 60/40 | 40/60 | 3-col | 4-col | custom]
│   │   ├── card.py            # ::: card [title="..."] [badge="..."] [icon="..."]
│   │   ├── stepper.py         # ::: stepper [id="..."] (sequential algorithmic phase walkthrough)
│   │   └── curtain.py         # ::: curtain (interactive before/after draggable split slider)
│   │
│   ├── # 🎛️ FAMILY 2: INTERACTIVE CONTROLS & LAB INPUTS (The Lab Atoms)
│   │   ├── slider.py          # ::: slider id="..." label="..." min=... max=... step=... [unit="..."]
│   │   ├── switch.py          # ::: switch id="..." label="..." [default=true|false]
│   │   ├── segments.py        # ::: segments id="..." (mutually exclusive pill button group)
│   │   ├── select.py          # ::: select id="..." label="..." options="..." (dropdown picker)
│   │   └── player.py          # ::: player target="..." (play/pause/step/reset animation transport)
│   │
│   └── # ⚡ FAMILY 3: EDITORIAL CONTENT & FEEDBACK
│       ├── plot.py            # ::: plot <script.py> (Barograph bridge + lightbox toggle)
│       ├── metrics.py         # ::: metrics (KPI / stat readout cards)
│       ├── tabs.py            # ::: tabs (tabbed multi-perspective switcher)
│       ├── accordion.py       # ::: accordion title="..." [open] (collapsible deep-dive)
│       ├── comparison.py      # ::: comparison (2-column before/after or A/B card)
│       └── callout.py         # ::: callout type=[note|tip|warning|danger]
│
├── server.py                  # HTTP live-reloading dev server
├── static/                    # Bundled CSS, JS runtime, and KaTeX
│   ├── katex/
│   ├── lantern.css            # Complete Obsidian Frost design system
│   └── lantern.js             # Client micro-runtime: scrollspy, toasts, sliders, event dispatch
└── templates/                 # Jinja2 layout templates
    ├── base.html.j2
    ├── explainer.html.j2      # Single-topic interactive paper layout
    ├── dashboard.html.j2      # Multi-card / multi-view hub layout
    └── optimization/          # Relocated optimization template (scaffoldable via 'lantern new')
        ├── explainer.md
        ├── widgets/
        │   ├── walker.js      # Relocated canvas walker
        │   └── barrier.js     # Relocated barrier lab
        └── plots/
            └── plot_rosenbrock.py
```

---

## 3. Specification: Family 1 — Layout & Spatial Chrome (Strips & Grids)

Standard Markdown only supports a single vertical column. `Lantern` solves this by providing spatial row and column strips:

### 3.1 The Grid Directive (`directives/grid.py`)
Allows authors to define multi-column horizontal strips.
```markdown
::: grid [preset | cols="..."] [gap="..."]
=== [Column Name]
Column 1 content (markdown, plots, or controls)...

=== [Column Name]
Column 2 content...
:::
```
**Supported Presets:**
- `50/50` (or `2-col`): `grid-template-columns: 1fr 1fr;`
- `60/40`: `grid-template-columns: 1.5fr 1fr;` (Ideal for: Plot on left, Controls on right)
- `40/60`: `grid-template-columns: 1fr 1.5fr;`
- `3-col` (or `33/33/33`): `grid-template-columns: repeat(3, 1fr);`
- `4-col`: `grid-template-columns: repeat(4, 1fr);`
- Custom: `cols="300px 1fr"` or `cols="2fr 1fr 1fr"`

**Sub-block delimiters:** Accepts either `=== [Title]` or `---` to separate columns inside the block. Automatically collapses to a clean single column on mobile screens (`< 768px`).

### 3.2 The Card Directive (`directives/card.py`)
A glassmorphic, bordered container box that can sit inside any grid column or document flow.
```markdown
::: card [title="Quadratic Programming (QP)"] [badge="Convex"] [icon="💎"]
A single smooth parabolic bowl. Solved in a finite number of active-set changes.
:::
```

### 3.3 The Stepper Directive (`directives/stepper.py`)
For algorithms that operate in distinct sequential phases (e.g. Simplex pivot steps, branch-and-bound exploration):
```markdown
::: stepper id="simplex-steps"
=== Step 1: Reduced Costs
Compute $r_N = c_N^T - c_B^T B^{-1} N$. Pick variable with most negative cost.

=== Step 2: Minimum Ratio Test
Determine outgoing basic variable to maintain primal feasibility.

=== Step 3: Basis Update
Perform row operations on the tableau to jump to the adjacent vertex.
:::
```
Emits a stepped progress bar with clickable phase indicators and forward/back navigation buttons.

### 3.4 The Curtain Directive (`directives/curtain.py`)
A draggable before/after split comparison slider:
```markdown
::: curtain
=== Before: Unconstrained Descent
Trapped in narrow parabolic oscillations.

=== After: Damped Newton-Raphson
Direct quadratic leap to the minimum.
:::
```

---

## 4. Specification: Family 2 — Interactive Controls & Lab Inputs (The Lab Atoms)

All controls in Family 2 automatically update a live value badge and emit a standardized browser event:
`window.dispatchEvent(new CustomEvent('lantern:input', { detail: { id, value } }))`
This allows any embedded simulation (Barograph plot, HTML5 canvas, or custom widget) to dynamically react to user input.

### 4.1 Sliders (`directives/slider.py`)
```markdown
::: slider id="alpha" label="Step Size α" min="0.0005" max="0.05" step="0.0005" default="0.005" [unit="s"]
:::
```
Emits `.lantern-slider` with a live number badge (`#val-alpha`) that updates synchronously on mouse drag.

### 4.2 Boolean Switches (`directives/switch.py`)
Smooth iOS-style animated toggle switch:
```markdown
::: switch id="damping" label="Enable Levenberg-Marquardt μI Damping" [default=true]
:::
```

### 4.3 Segmented Pill Selectors (`directives/segments.py`)
Mutually exclusive tactile pill button strip:
```markdown
::: segments id="algorithm" default="gd"
- [gd]: Gradient Descent
- [armijo]: Armijo Line Search
- [newton]: Newton-Raphson
- [bfgs]: Quasi-Newton BFGS
:::
```

### 4.4 Dropdown Selectors (`directives/select.py`)
```markdown
::: select id="landscape" label="Optimization Terrain" default="rosenbrock"
- [rosenbrock]: Rosenbrock Banana Valley
- [ellipse]: Ill-Conditioned Ellipse (κ = 40)
- [rastrigin]: Rastrigin Multimodal Surface
- [saddle]: Hyperbolic Saddle Point
:::
```

### 4.5 Simulation Transport Player (`directives/player.py`)
A media playback bar for time-stepping algorithms and ODE simulations:
```markdown
::: player id="sim-player" target="opt-canvas" [speeds="0.5x, 1x, 2x, 5x"]
:::
```
Renders: `[ ⏮ Reset ] [ ⏯ Play/Pause ] [ ⏭ Step ]`, speed selector dropdown, and an iteration scrubber.

---

## 5. Specification: Family 3 — Editorial Content, Feedback & Micro-Interactions

### 5.1 Barograph Plot Bridge with Lightbox (`directives/plot.py`)
```markdown
::: plot <script.py> [backend=plotly|svg] [height=500px] [title="Optional Title"]
:::
```
- Executes via `Barograph` (in-process `import barograph` with subprocess fallback).
- Injects a full-screen expand button in the corner that opens the plot in a high-res lightbox modal.

### 5.2 KPI / Metric Cards (`directives/metrics.py`)
```markdown
::: metrics [cols=4]
- Iterations: 42
- Optimal Cost f(x*): 0.0024
- Gradient Norm ‖∇f‖: 1.4e-5
- Status: Converged [badge=emerald]
:::
```

### 5.3 Tab Groups (`directives/tabs.py`)
```markdown
::: tabs
=== Intuition
Walking downhill in thick fog...

=== Mathematical Derivation
The step update is given by:
$$x_{k+1} = x_k - \alpha_k \nabla f(x_k)$$

=== Simulation
::: plot plot_gradient_descent.py
:::
:::
```

### 5.4 Collapsible Deep-Dives (`directives/accordion.py`)
```markdown
::: accordion title="Proof of Quadratic Convergence for Pure Newton" [open]
Under Lipschitz continuous Hessian assumptions...
$$ \|x_{k+1} - x^*\| \le \frac{1}{2} M \|H(x^*)^{-1}\| \|x_k - x^*\|^2 $$
:::
```

### 5.5 Side-by-Side Comparison (`directives/comparison.py`)
```markdown
::: comparison
=== Left: Gradient Descent
- O(n) memory
- Linear convergence rate

=== Right: Newton-Raphson
- O(n³) Hessian solve
- Quadratic local convergence
:::
```

### 5.6 Alerts / Callouts (`directives/callout.py`)
```markdown
::: callout type=[note|tip|warning|danger] [title="Optional"]
Message content...
:::
```

### 5.7 Toast System & Inline Tooltips
In `lantern.js`:
- **Toast Notifications:** Provide `window.lantern.toast(message, type="info"|"success"|"warning"|"error")`. Spawns a sleek, floating glassmorphic snackbar at the bottom right that auto-fades in 3 seconds.
- **Heading Permalink Anchors:** Hovering over any `h2`, `h3`, `h4` reveals a `#` link icon. Clicking it copies the anchor URL to the clipboard and triggers `lantern.toast("Anchor link copied to clipboard", "success")`.
- **Inline Tooltips:** Pattern `[?term: definition text]` converts into an underlined term with a floating hover popover.

---

## 6. Page Layouts & Snowpack Companion Integration

In `src/lantern/templates/explainer.html.j2`:
1. **Sticky Top Navbar:**
   - Left: Brand icon (`🏮`) and Document Title.
   - Center: Dynamic breadcrumbs or active section scrollspy.
   - Right: Reading progress bar indicator, theme switch, and Snowpack PDF button.
2. **Snowpack Companion Button:**
   If document frontmatter includes `snowpack_pdf: "report.pdf"`, render:
   ```html
   <a class="lantern-btn lantern-btn-primary" href="{{ snowpack_pdf }}" target="_blank">
     📄 Open Companion PDF Reader (Snowpack)
   </a>
   ```
3. **Reading Progress Bar:** A thin laser progress bar across the very top of the window tracking scroll percentage (`0% → 100%`).
4. **Footer:** Attributions, license, and link back to Frost/TU Delft repository.

---

## 7. Relocating Course-Specific Widgets (Preserving the Good Work)

Do **not** discard `walker.js`, `barrier.js`, or `decision.js`! They are well-engineered. Relocate them cleanly:
1. Create `src/lantern/templates/optimization/`:
   - Place a complete starter workspace with `explainer.md`, `widgets/walker.js`, `widgets/barrier.js`, and sample plot scripts.
   - Wire `lantern new my-lab --template optimization` to scaffold this starter.
2. Create `examples/optimization/`:
   - Keep a working demo project in the repository root that can be built and previewed to verify `Lantern`'s capabilities.
3. Remove `src/lantern/directives/walker.py`, `barrier.py`, and `decision.py`.
4. Remove `walker.js`, `barrier.js`, and `decision.js` from `src/lantern/static/`.

---

## 8. Verification Checklist

1. **Unit & Directive Tests:**
   - Update `tests/test_directives.py` to test:
     - `grid` (verifies 50/50, 60/40, and 3-col outputs).
     - `card`
     - `slider`
     - `switch`
     - `segments`
     - `metrics`
     - `tabs`
     - `accordion`
     - `callout`
     - `plot`
   - Run `pytest` and ensure all tests pass 100%.
2. **End-to-End Build Test:**
   - Run `lantern build examples/optimization/explainer.md -o dist/`.
   - Open the resulting HTML and verify that layout grids (e.g. 60/40 plot + slider controls), math formulas, and tabs render flawlessly.
3. **Hermetic Nix Check:**
   - Run `nix flake check` to verify clean build without warnings.
