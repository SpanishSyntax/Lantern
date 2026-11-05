"""Scaffolding utilities for Lantern workspaces and projects."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from lantern.compiler import LanternCompiler


def create_project(
    name: str,
    template: str = "explainer",
    parent_dir: Path | None = None,
) -> dict[str, Any]:
    """Scaffold a new explainer, simulation dashboard, or domain lab workspace.

    Args:
        name: Name of the workspace directory to create.
        template: Starter template ('explainer', 'dashboard', 'optimization').
        parent_dir: Optional base directory to place the project in (default: cwd).

    Returns:
        Structured result dict with status, paths, and scaffolded files.
    """
    clean_name = name.strip()
    if not clean_name:
        return {"status": "error", "error": "Missing or empty 'name' argument."}

    template_type = (template or "explainer").lower().strip()
    base_dir = parent_dir if parent_dir is not None else Path.cwd()
    target_dir = base_dir / clean_name

    if target_dir.exists():
        return {"status": "error", "error": f"Directory '{clean_name}' already exists."}

    target_dir.mkdir(parents=True, exist_ok=True)
    compiler = LanternCompiler()

    if template_type == "optimization":
        opt_template_dir = compiler.template_dir / "optimization"
        if opt_template_dir.exists():
            shutil.copytree(opt_template_dir, target_dir, dirs_exist_ok=True)
            (target_dir / ".gitignore").write_text(
                "dist/\n__pycache__/\n*.html\n", encoding="utf-8"
            )
            files = [str(p.relative_to(target_dir)) for p in target_dir.rglob("*") if p.is_file()]
            return {
                "status": "ok",
                "name": clean_name,
                "template": template_type,
                "directory": str(target_dir),
                "target_file": str(target_dir / "explainer.md"),
                "files": files,
            }

    # Sample Barograph plotting script
    sample_plot_py = """import numpy as np
import plotly.graph_objects as go

x = np.linspace(-2.0, 2.0, 80)
y = np.linspace(-1.0, 3.0, 80)
X, Y = np.meshgrid(x, y)
Z = np.log10((1.0 - X) ** 2 + 100.0 * (Y - X ** 2) ** 2 + 1.0)

fig = go.Figure(
    data=[go.Surface(x=X, y=Y, z=Z, colorscale="Viridis", showscale=False)]
)
fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=0, r=0, t=30, b=0),
)
"""

    if template_type == "dashboard":
        md_file = target_dir / "dashboard.md"
        content = f"""---
title: "{clean_name.title()} Simulation Dashboard"
subtitle: "Interactive Multi-Method Exploration Deck"
template: dashboard
---

::: grid 60/40
=== Live Simulation Deck
::: plot plot_optimization.py backend=plotly height=480px title="System Phase Manifold"
:::

=== Control Center
::: card title="Lab Controls" badge="Active" icon="🎛️"
::: slider id="step-size" label="Simulation Step Size" min="0.001" max="0.1" step="0.005" default="0.01" unit="s"
:::

::: switch id="damping-toggle" label="Enable Damping Regularization" default=true
:::

::: segments id="mode-selector" default="mode-a"
- [mode-a]: Mode A (Standard)
- [mode-b]: Mode B (High-Precision)
:::
:::
:::

::: metrics cols=4
- Iterations: 120
- State Norm: 0.0042
- Latency: 1.2ms [badge=emerald]
- System Health: Nominal [badge=cyan]
:::
"""
    else:
        md_file = target_dir / "explainer.md"
        content = f"""---
title: "{clean_name.title()} Interactive Explainer"
subtitle: "A Mathematical Deep-Dive with Live Visualizations"
author: "Frost Research Group"
template: explainer
---

# Introduction

Welcome to **{clean_name.title()}**. This document is an interactive scientific explainer compiled with `Lantern`.

::: callout type=note title="Interactive Document"
Features multi-column spatial strips, live parameter sliders, tabs, and client-side KaTeX math ($x_{{k+1}} = x_k - \\alpha \\nabla f(x_k)$).
:::

::: grid 60/40
=== 3D Surface
::: plot plot_optimization.py backend=plotly height=460px title="Objective Surface"
:::

=== Parameter Lab
::: card title="Sensitivity Parameters" badge="Interactive" icon="⚡"
Adjust real-time parameters below:

::: slider id="alpha" label="Step Size α" min="0.0001" max="0.01" step="0.0005" default="0.002" unit="s"
:::

::: switch id="momentum" label="Enable Polyak Momentum" default=true
:::
:::
:::

::: comparison
=== Left: Method A (First-Order)
- Linear convergence rate $O(1/k)$
- Low memory overhead $O(n)$

=== Right: Method B (Second-Order)
- Quadratic local convergence
- Requires curvature matrix solve
:::
"""

    (target_dir / "plot_optimization.py").write_text(sample_plot_py, encoding="utf-8")
    md_file.write_text(content, encoding="utf-8")
    (target_dir / ".gitignore").write_text("dist/\n__pycache__/\n*.html\n", encoding="utf-8")

    files = [str(p.relative_to(target_dir)) for p in target_dir.rglob("*") if p.is_file()]
    return {
        "status": "ok",
        "name": clean_name,
        "template": template_type,
        "directory": str(target_dir),
        "target_file": str(md_file),
        "files": files,
    }
