# 🏮 Lantern

> Frost's Interactive Explainer & Simulation Dashboard Compiler

`Lantern` is the interactive counterpart to `Snowpack`. Where `Snowpack` compiles static, publication-grade PDFs (Typst/LaTeX), `Lantern` compiles and serves **dynamic, interactive web explainers and simulation dashboards** (DOM, HTML5 Canvas, live parameter sliders, KaTeX math, and Plotly embeds).

---

## ⚡ Core Principles

- **Zero npm / Node Dependencies:** 100% pure Python 3.12+ and Nix. Sub-100ms compilation times.
- **Standalone Delivery:** Emits single, self-contained `.html` files with embedded CSS, KaTeX math, and JavaScript widgets.
- **Built-in Live Serving (`lantern serve`):** An integrated HTTP server with SSE browser synchronization that watches both Markdown documents and referenced Python plotting scripts.
- **Deep Barograph Integration:** Calls `barograph` in-process (or via CLI) to execute simulations and embed figures seamlessly.

---

## 🚀 Quick Start

### 1. Scaffold a New Project
```bash
lantern new optimization-lab --template explainer
cd optimization-lab
```

### 2. Live Preview with Auto-Reload
```bash
lantern serve explainer.md
```
Watches `explainer.md`, referenced Python plot scripts, and updates the browser instantly.

### 3. Build Standalone Production HTML
```bash
lantern build explainer.md -o dist/ --standalone
```

---

## 🧩 Markdown Directives & UI Components

Lantern extends Python-Markdown with built-in obsidian-styled components and reactive widgets:

### 📐 Layout Strips & Chrome
- **`::: grid [50/50 | 60/40 | 40/60 | 3-col | 33/33/33 | 4-col]`**: Responsive equal-height grid columns delimited with `=== [Title]`.
- **`::: card [title="..."] [badge="..."] [icon="..."]`**: Glassmorphic elevated container card.
- **`::: stepper id="..."`**: Zero-jerk progressive phase walkthrough using CSS Grid stacking. Steps separated with `=== Step N: Title`.
- **`::: curtain [before="Before"] [after="After"]`**: Side-by-side or split comparison card.

### 🎛️ Interactive Controls & Lab Inputs
- **`::: slider id="..." label="..." min=.. max=.. step=.. default=.. [unit="..."]`**: Live parameter slider emitting `lantern:input` DOM events.
- **`::: switch id="..." label="..." [default=true|false]`**: Boolean reactive toggle switch.
- **`::: segments id="..." default="..."`**: Pill button selector with `- [key]: Label` options.
- **`::: select id="..." label="..." [default="..."]`**: Dropdown select with `- [key]: Label` options.
- **`::: player id="..." target="..." speeds="0.5x, 1x, 2x, 5x"`**: Media scrub bar with reset, play/pause, step controls.

### ⚡ Editorial & Visual Content
- **`::: plot <script.py> [backend=plotly|svg] [height=500px] [title="..."]`**: In-process Barograph execution with Plotly interactive embeds or vector SVG.
- **`::: tabs`**: Tab switcher with `=== Tab Name` panes.
- **`::: accordion title="..." [open=true|false]`**: Collapsible technical proof or appendix card.
- **`::: metrics [cols=2|3|4]`**: KPI status readout strip with `- Key: Value [badge=emerald|cyan|purple|amber|rose]`.
- **`::: comparison`**: Method A vs Method B comparative trade-off container with `=== Left: ...` and `=== Right: ...`.
- **`::: callout type=[note|tip|warning|danger] [title="..."]`**: Alert callout box.
- **`[?term: hint]`**: Inline hover tooltip for technical nomenclature.
- **Floating Dot Rail**: Automatic ScrollSpy navigation rail dynamically populated from `## Heading` sections.

### 🧪 Algorithmic Lab Widgets
- **`::: canvas-walker [landscape=rosenbrock|ellipse|rastrigin|saddle] [algorithms=gd,armijo,newton,bfgs,momentum]`**: Interactive HTML5 canvas with real-time gradient descent/Newton simulation.
- **`::: barrier-vs-penalty`**: Interactive constraint boundary lab with penalty multiplier slider and contour slice.
- **`::: decision-ladder questions=<questions.json>`**: Interactive step-by-step decision flowchart wizard.

---

## 🛠️ CLI Reference

```text
lantern new <name> [--template explainer|dashboard]
lantern build [file.md] [-o dist/] [--standalone] [--template explainer|dashboard]
lantern serve [file.md] [-p PORT] [--no-open] [--host HOST]
lantern status
lantern list
```

---

## ❄️ Nix Integration

Lantern is packaged for Nix Flakes and Frost fleets:

```bash
nix run github:SpanishSyntax/Lantern -- new my-explainer
nix shell github:SpanishSyntax/Lantern
```
