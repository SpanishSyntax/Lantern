<p align="center">
  <img src="assets/banner.png" alt="Glowing polar expedition lantern casting warm illumination across arctic campsite" width="100%" />
</p>

# Lantern 🏮

> Interactive Explainer & Simulation Dashboard Compiler

Lantern is the dynamic counterpart to Snowpack. Where Snowpack compiles static, publication-grade PDFs, Lantern compiles and serves interactive web explainers and simulation dashboards featuring reactive DOM components, HTML5 Canvas physics, parameter sliders, KaTeX mathematics, and live Plotly embeds.

---

## Why "Lantern"? (The Lore)

> **lantern** (`/ˈlæn.tərn/`) — *noun:* A storm-proof, glass-shielded flame carried by hand through polar darkness, casting warm, revealing light on intricate mechanisms and icy footpaths.

Where static maps and printed books record fixed terrain, a traveler in the dark needs an active lantern to illuminate interactive choices, examine moving machinery, and test footing in real time.

Lantern illuminates dynamic computational models:
- **Interactive Counterpart**: Where static document compilers generate fixed PDFs, Lantern compiles live, browser-based simulation dashboards and algorithmic explainers.
- **Responsive Controls**: Embeds parameter sliders, KaTeX mathematical notation, Plotly visualizations, and canvas ODE numerical models directly into lightweight web artifacts.

---

## Core Principles

- **Zero Node or npm Dependencies**: Pure Python 3.12+ and Nix architecture with sub-100ms compilation times.
- **Standalone Delivery**: Emits self-contained `.html` bundles with inlined CSS, KaTeX math engines, and JavaScript widgets.
- **Built-in Live Server**: Integrated HTTP server with Server-Sent Events (SSE) synchronization that watches Markdown files and referenced Python simulation scripts.
- **Deep Barograph Integration**: In-process execution of Barograph plotting scripts, syncing interactive sliders with Plotly frames and vector figures.
- **Model Context Protocol (MCP)**: Native stdio server exposing project creation, document compilation, and development server management to AI agents.

---

## Widget Ecosystem

| Category | Directives | Function |
| :--- | :--- | :--- |
| **Layout** | `::: grid`, `::: card`, `::: stepper`, `::: curtain` | Responsive columns, zero-jerk stepped walkthroughs, before/after comparisons |
| **Controls** | `::: slider`, `::: switch`, `::: segments`, `::: select`, `::: player` | Parameter sweeps emitting reactive DOM events (`lantern:input`) |
| **Visual Content** | `::: plot`, `::: math-plot`, `::: widget`, `::: tabs`, `::: accordion` | In-process Barograph plots, 60 FPS client math evaluators, collapsible proofs |
| **Lab Simulation** | `::: canvas-walker`, `::: barrier-vs-penalty`, `::: decision-ladder` | Real-time gradient descent simulation, constraint penalty sweeps, decision trees |

---

## Quick Navigation

- [Getting Started](getting-started.md): Installation via Nix or pip, scaffolding starter explainers, and dev server usage.
- [Architecture & Pipeline](architecture.md): Parsing AST, reactive event dispatch, Barograph runtime, and standalone bundling.
- [Directives & Components](usage.md): Syntax reference for every layout strip, input control, and simulation widget.
- [Configuration & API Reference](api.md): Project configuration schema, DOM event protocol, and Python API reference.
