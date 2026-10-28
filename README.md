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

## 🧩 Markdown Directives

Lantern extends Python-Markdown with custom `:::` blocks:

### `::: plot <script.py> [backend=plotly|svg] [height=500px]`
Executes the plotting script via `barograph` (in-process or subprocess fallback) and embeds the Plotly interactive div or inline vector SVG.

```markdown
::: plot plot_optimization.py backend=plotly height=520px
:::
```

### `::: canvas-walker [landscape=rosenbrock|ellipse|rastrigin|saddle] [algorithms=gd,armijo,newton,bfgs,momentum]`
Injects a high-DPI HTML5 interactive canvas with real-time gradient descent/Newton simulation, click-to-seed coordinate picker, and live readout metrics.

```markdown
::: canvas-walker landscape=rosenbrock algorithms=gd,armijo,newton,bfgs,momentum
:::
```

### `::: barrier-vs-penalty`
Injects the interactive constraint boundary lab with a real-time penalty/barrier multiplier slider and 2D contour + 1D cross-section slice plots.

```markdown
::: barrier-vs-penalty
:::
```

### `::: decision-ladder questions=<questions.json>`
Injects an interactive step-by-step decision flowchart wizard for algorithmic selection.

```markdown
::: decision-ladder questions=questions.json
:::
```

### `::: callout type=[note|tip|warning|danger]`
GitHub/Frost style alert callouts.

```markdown
::: callout type=tip
Second-order methods like Newton-Raphson achieve quadratic convergence near the optimum.
:::
```

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
