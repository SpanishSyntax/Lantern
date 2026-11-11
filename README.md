<p align="center">
  <img src="assets/banner.png" alt="Glowing polar expedition lantern casting warm illumination across arctic campsite" width="100%" />
</p>

# Lantern 🏮

> Frost's Interactive Explainer & Simulation Dashboard Compiler

Lantern is the interactive counterpart to Snowpack. Where Snowpack compiles static, publication-grade PDFs (Typst/LaTeX), Lantern compiles and serves dynamic, interactive web explainers and simulation dashboards featuring reactive DOM components, HTML5 Canvas physics, live parameter sliders, KaTeX math, and Plotly embeds.

[![Documentation](https://img.shields.io/badge/docs-GitHub_Pages-blue.svg)](https://spanishsyntax.github.io/Lantern)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## Why "Lantern"? (The Lore)

> **lantern** (`/ˈlæn.tərn/`) — *noun:* A storm-proof, glass-shielded flame carried by hand through polar darkness, casting warm, revealing light on intricate mechanisms and icy footpaths.

Where static maps and printed books record fixed terrain, a traveler in the dark needs an active lantern to illuminate interactive choices, examine moving machinery, and test footing in real time.

Lantern illuminates dynamic computational models:
- **Interactive Counterpart**: Where static document compilers generate fixed PDFs, Lantern compiles live, browser-based simulation dashboards and algorithmic explainers.
- **Responsive Controls**: Embeds live parameter sliders, KaTeX mathematical notation, Plotly visualizations, and canvas ODE numerical models directly into lightweight web artifacts.

---

## Core Principles

- **Zero Node or npm Dependencies**: Pure Python 3.12+ and Nix architecture with sub-100ms compilation times.
- **Standalone Delivery**: Emits single, self-contained `.html` files with inlined CSS, KaTeX math, and JavaScript widgets.
- **Built-in Live Serving**: Integrated HTTP server with Server-Sent Events (SSE) synchronization that watches Markdown documents and referenced Python plotting scripts.
- **Deep Barograph Integration**: Executes standalone Barograph scripts in-process to embed interactive vector and Plotly visualizations.

---

## Documentation

Full documentation, directive guides, architecture details, and API references are available on the **[Documentation Site](https://spanishsyntax.github.io/Lantern)**:

- [Getting Started](https://spanishsyntax.github.io/Lantern/#/getting-started)
- [Architecture & Pipeline](https://spanishsyntax.github.io/Lantern/#/architecture)
- [Directives & Components](https://spanishsyntax.github.io/Lantern/#/usage)
- [Configuration & API Reference](https://spanishsyntax.github.io/Lantern/#/api)

---

## Quick Start

### 1. Scaffold a New Project

```bash
lantern new optimization-lab --template explainer
cd optimization-lab
```

### 2. Live Preview with Auto-Reload

```bash
lantern serve explainer.md
```

Watches `explainer.md` and referenced Python plot scripts, updating connected browser tabs instantly.

### 3. Build Standalone Production HTML

```bash
lantern build explainer.md -o dist/ --standalone
```

---

## Markdown Directives and UI Components

Lantern extends Markdown with structured directives and reactive widgets:

### Layout Strips
- `::: grid [50/50 | 60/40 | 40/60 | 3-col | 4-col]`: Responsive multi-column layout.
- `::: card [title="..."] [badge="..."]`: Elevated container card.
- `::: stepper id="..."`: Progressive phased derivation cards.
- `::: curtain [before="..."] [after="..."]`: Split before/after comparison.

### Interactive Controls
- `::: slider id="..." label="..." min=.. max=.. step=.. default=..`: Live parameter slider emitting `lantern:input` DOM events.
- `::: switch id="..." label="..." [default=true|false]`: Boolean reactive toggle switch.
- `::: segments id="..." default="..."`: Segmented button pill selector.
- `::: select id="..." label="..." [default="..."]`: Dropdown selection box.

### Visual and Editorial Content
- `::: plot <script.py> [backend=plotly|svg] [height=500px]`: In-process Barograph plot execution.
- `::: math-plot fn="..." [domain="min, max"] [height=360px]`: 60 FPS client-side mathematical curve renderer.
- `::: metrics [cols=2|3|4]`: Status readout strip with status badges.
- `::: tabs`: Multi-tab pane switcher.
- `::: accordion title="..." [open=true|false]`: Collapsible technical derivation card.

### Algorithmic Lab Widgets
- `::: canvas-walker [landscape=rosenbrock|ellipse|rastrigin|saddle]`: 2D optimization simulator on HTML5 canvas.
- `::: barrier-vs-penalty`: Logarithmic barrier vs penalty constraint sweep lab.

---

## CLI Overview

```text
Usage:
  lantern [file] [options]             Interactive status or default compile
  lantern build [file] [options]       Compile Markdown into optimized HTML
  lantern export [file] [options]      Export static bundle or Jinja2 project
  lantern serve [file] [options]       Spin up dev server with live-reloading
  lantern new <name> [options]         Scaffold a starter project
  lantern status                       Display telemetry and backend status
  lantern list                         List available templates and documents
  lantern mcp                          Run Model Context Protocol stdio server
```

---

## Nix Flake Configuration

```nix
{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    lantern.url = "github:SpanishSyntax/Lantern";
    lantern.inputs.nixpkgs.follows = "nixpkgs";
  };
}
```

---

## License

MIT © [SpanishSyntax](https://github.com/SpanishSyntax)
