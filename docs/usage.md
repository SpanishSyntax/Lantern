# Directives & Components

Lantern extends Markdown with high-level directives for layout grids, interactive parameter controls, computational plots, and algorithmic labs.

---

## Layout Directives

### Grid (`::: grid`)

Constructs responsive multi-column layouts. Columns are delimited by `=== [Title]`.

```markdown
::: grid 50/50
=== Left Column
Content in the first column with standard markdown.

=== Right Column
Content in the second column.
:::
```

Supported column proportions: `50/50`, `60/40`, `40/60`, `33/33/33`, `3-col`, `4-col`.

### Card (`::: card`)

Renders a glassmorphic elevated container card with optional header, badge, and icon.

```markdown
::: card title="State Space Representation" badge="Core Model"
The system dynamics are governed by:
$$ \dot{\mathbf{x}} = \mathbf{A}\mathbf{x} + \mathbf{B}\mathbf{u} $$
:::
```

### Stepper (`::: stepper`)

Generates a zero-jerk progressive phase walkthrough. Ideal for derivations or multi-stage algorithms.

```markdown
::: stepper id="gd-derivation"
=== Step 1: Objective Function
Define the quadratic objective $f(x) = \frac{1}{2} x^T Q x - b^T x$.

=== Step 2: Gradient Calculation
Compute the first-order gradient $\nabla f(x) = Q x - b$.

=== Step 3: Update Step
Apply the descent direction $x_{k+1} = x_k - \alpha \nabla f(x_k)$.
:::
```

### Curtain (`::: curtain`)

Provides an interactive before/after split comparison.

```markdown
::: curtain before="Standard Gradient Descent" after="Nesterov Accelerated Gradient"
Left side demonstrates standard oscillations.
===
Right side demonstrates accelerated momentum dampening.
:::
```

---

## Interactive Controls

Input directives bind to the `lantern:input` reactive bus:

### Slider (`::: slider`)

```markdown
::: slider id="learning_rate" label="Learning Rate (\alpha)" min=0.001 max=0.1 step=0.005 default=0.02 unit=""
:::
```

### Switch (`::: switch`)

```markdown
::: switch id="enable_momentum" label="Enable Momentum" default=true
:::
```

### Segmented Buttons (`::: segments`)

```markdown
::: segments id="optimizer" default="adam"
- [sgd]: SGD
- [momentum]: Momentum
- [adam]: Adam
:::
```

### Dropdown Select (`::: select`)

```markdown
::: select id="landscape" label="Loss Surface" default="rosenbrock"
- [rosenbrock]: Rosenbrock Valley
- [rastrigin]: Rastrigin Multimodal
- [saddle]: Monkey Saddle
:::
```

---

## Visual and Editorial Content

### Barograph Plot (`::: plot`)

Executes a standalone Python plotting script in-process and embeds the resulting figure:

```markdown
::: plot plot_optimization.py backend=plotly height=480px title="Convergence History"
:::
```

Options:
- `backend`: `plotly` (interactive webGL/SVG) or `svg` (pure static vector)
- `height`: Pixel or CSS height (e.g. `500px`)
- `title`: Header caption displayed above the plot canvas

### Fast Math Plot (`::: math-plot`)

Evaluates analytical mathematical functions in the browser at 60 FPS, responding to slider parameters:

```markdown
::: math-plot fn="sin(a * x) * exp(-b * x)" domain="-5, 5" height=360px title="Damped Harmonic Response"
:::
```

### Metrics Strip (`::: metrics`)

Renders a KPI readout dashboard:

```markdown
::: metrics cols=3
- Convergence Epochs: 42 [badge=emerald]
- Final Loss: 1.24e-5 [badge=cyan]
- Optimality Gap: 0.00% [badge=purple]
:::
```

### Tabs & Accordions

```markdown
::: tabs
=== Formulation
Mathematical formulation and theorem statement.
=== Implementation
Python or Rust implementation snippet.
:::

::: accordion title="Detailed Convergence Proof" open=false
Step-by-step mathematical derivation of the contraction mapping.
:::
```

---

## Algorithmic Lab Widgets

### Canvas Walker (`::: canvas-walker`)

An interactive HTML5 canvas simulating 2D optimization paths across analytical surfaces:

```markdown
::: canvas-walker landscape=rosenbrock algorithms=gd,momentum,newton
:::
```

### Constraint Lab (`::: barrier-vs-penalty`)

Demonstrates logarithmic barrier vs quadratic penalty functions with interactive multiplier sweeps:

```markdown
::: barrier-vs-penalty
:::
```

---

## CLI Commands and Options

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

Options:
  -o, --output PATH      Specify output HTML filename or export directory
  -t, --template NAME    Layout template: 'explainer' (default), 'dashboard', 'optimization'
  --format FORMAT        Export format: 'static' (default) or 'jinja'
  --standalone           Inline CSS, KaTeX math, and JavaScript into a single file
  -p, --port PORT        Dev server HTTP port (default: 8080)
  --host HOST            Dev server host (default: 127.0.0.1)
  --no-open              Do not automatically open browser on launch
  -A, --agent            Machine/agent-friendly output mode
  --json                 Output structured JSON payloads
```
