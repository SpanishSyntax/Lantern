"""CLI commands, router, and Prism status dashboard for Lantern."""

from __future__ import annotations

import argparse
import os
import platform
import sys
from pathlib import Path
from typing import Any, Sequence

from lantern import __version__
from lantern.compiler import LanternCompiler
from lantern.server import LanternDevServer

# Prism UI integration with graceful ANSI fallback
try:
    from prism import UI, render_panel  # type: ignore

    ui = UI(app_name="lantern", icon="🏮", badge_color="1;36")
except ImportError:
    class FallbackUI:
        def badge(self) -> str:
            return "\033[1;36m[🏮 lantern]\033[0m"

        def bold(self, text: str) -> str:
            return f"\033[1m{text}\033[0m"

        def cyan(self, text: str) -> str:
            return f"\033[36m{text}\033[0m"

        def green(self, text: str) -> str:
            return f"\033[32m{text}\033[0m"

        def yellow(self, text: str) -> str:
            return f"\033[33m{text}\033[0m"

        def red(self, text: str) -> str:
            return f"\033[31m{text}\033[0m"

        def dim(self, text: str) -> str:
            return f"\033[2m{text}\033[0m"

        def success(self, msg: str) -> None:
            print(f"{self.badge()} \033[32m✓\033[0m {msg}")

        def info(self, msg: str) -> None:
            print(f"{self.badge()} \033[36mℹ\033[0m {msg}")

        def warn(self, msg: str) -> None:
            print(f"{self.badge()} \033[33m⚠\033[0m {msg}")

        def error(self, msg: str) -> None:
            print(f"{self.badge()} \033[31m✗\033[0m {msg}", file=sys.stderr)

    ui = FallbackUI()  # type: ignore

    def render_panel(
        title: str,
        lines: Sequence[str] | str,
        border_color: str = "0;36",
        width: int = 76,
        stream: Any = None,
        **kwargs: Any,
    ) -> None:
        out = stream or sys.stdout
        body_lines = lines.splitlines() if isinstance(lines, str) else list(lines)
        box_w = max(40, width)
        inner_w = box_w - 4
        title_seg = f" {title} " if title else ""
        top_fill = max(1, box_w - 3 - len(title) - (2 if title else 0))
        top = f"\033[{border_color}m╭─\033[0m\033[1m{title_seg}\033[0m\033[{border_color}m{'─' * top_fill}╮\033[0m"
        bottom = f"\033[{border_color}m╰{'─' * (box_w - 2)}╯\033[0m"
        side = f"\033[{border_color}m│\033[0m"
        print(top, file=out)
        for raw_line in body_lines:
            import re
            plain = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", raw_line)
            pad = " " * max(0, inner_w - len(plain))
            print(f"{side} {raw_line}{pad} {side}", file=out)
        print(bottom, file=out)


def find_default_target() -> Path | None:
    """Find target markdown file in current directory."""
    cwd = Path.cwd()
    for candidate in ("explainer.md", "dashboard.md", "index.md", "README.md"):
        p = cwd / candidate
        if p.exists():
            return p
    md_files = list(cwd.glob("*.md"))
    if md_files:
        return sorted(md_files)[0]
    return None


def cmd_new(args: argparse.Namespace) -> int:
    """Scaffold a new explainer or simulation dashboard project."""
    name: str = args.name
    template_type: str = (args.template or "explainer").lower()
    target_dir = Path.cwd() / name

    if target_dir.exists():
        ui.error(f"Directory '{name}' already exists.")
        return 1

    target_dir.mkdir(parents=True, exist_ok=True)

    # Sample Barograph plotting script
    sample_plot_py = """import numpy as np
import plotly.graph_objects as go

# Objective Surface: Rosenbrock Banana Function
# f(x, y) = (1 - x)^2 + 100 * (y - x^2)^2
x = np.linspace(-2.0, 2.0, 100)
y = np.linspace(-1.0, 3.0, 100)
X, Y = np.meshgrid(x, y)
Z = (1.0 - X) ** 2 + 100.0 * (Y - X ** 2) ** 2

# Log surface for clean visual contours
Z_log = np.log10(Z + 1.0)

fig = go.Figure()

# Add 3D surface
fig.add_trace(
    go.Surface(
        x=X,
        y=Y,
        z=Z_log,
        colorscale="Viridis",
        showscale=False,
        opacity=0.9,
    )
)

# Annotate global minimum at (1, 1)
fig.add_trace(
    go.Scatter3d(
        x=[1.0],
        y=[1.0],
        z=[0.0],
        mode="markers+text",
        marker=dict(size=6, color="#34d399"),
        text=["x* (1, 1)"],
        textposition="top center",
        name="Global Min",
    )
)

fig.update_layout(
    title="Rosenbrock Valley Objective Surface (Log Scale)",
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    scene=dict(
        xaxis=dict(title="X", backgroundcolor="#0b0f17", gridcolor="#1e293b"),
        yaxis=dict(title="Y", backgroundcolor="#0b0f17", gridcolor="#1e293b"),
        zaxis=dict(title="log10(f + 1)", backgroundcolor="#0b0f17", gridcolor="#1e293b"),
    ),
    margin=dict(l=0, r=0, t=40, b=0),
)
"""

    if template_type == "dashboard":
        md_file = target_dir / "dashboard.md"
        content = f"""---
title: "{name.title()} Simulation Dashboard"
subtitle: "Interactive Multi-Method Optimization Lab"
template: dashboard
---

## Real-Time Simulation Deck

Welcome to the **{name.title()}** dashboard. This workspace provides real-time parameter exploration, gradient flow simulation, and constraint relaxation studies.

::: plot plot_optimization.py backend=plotly height=500px
:::

<div class="lantern-grid-2">
  <div>
    <h3>Trajectory Convergence Walker</h3>
    <p>Simulate gradient descent, Armijo backtracking, and Newton's method simultaneously across the objective landscape.</p>
    ::: canvas-walker landscape=rosenbrock algorithms=gd,armijo,newton,bfgs,momentum
    :::
  </div>

  <div>
    <h3>Constraint Boundary Lab</h3>
    <p>Compare exterior penalty walls versus interior barrier singularities under dynamic parameter variation.</p>
    ::: barrier-vs-penalty
    :::
  </div>
</div>

::: callout type=tip
Use `lantern serve dashboard.md` to start the live synchronization engine while tweaking parameters in `plot_optimization.py`.
:::
"""
    else:
        md_file = target_dir / "explainer.md"
        content = f"""---
title: "{name.title()} Interactive Explainer"
subtitle: "A Mathematical Deep-Dive with Live Visualizations"
author: "Frost Research Group"
template: explainer
---

# Introduction

In numerical optimization, solving unconstrained minimization problems:

$$\\min_{{x \\in \\mathbb{{R}}^n}} f(x)$$

requires navigating complex curvature, ill-conditioned valleys, and local extrema.

::: callout type=note
This document features live, client-side KaTeX rendering ($...$ and $$...$$), interactive HTML5 canvas simulation walkers, and embedded Plotly surfaces.
:::

## 1. Objective Surface & Curvature

The classical test landscape for unconstrained optimization is the **Rosenbrock Valley function**:

$$f(x, y) = (1 - x)^2 + 100(y - x^2)^2$$

Its gradient is given by:

$$\\nabla f(x, y) = \\begin{{bmatrix}} -2(1 - x) - 400x(y - x^2) \\\\ 200(y - x^2) \\end{{bmatrix}}$$

Below is the live 3D surface rendered directly from `plot_optimization.py`:

::: plot plot_optimization.py backend=plotly height=520px
:::

## 2. Interactive Algorithmic Walker

Test first-order gradient descent versus second-order Newton-Raphson and Quasi-Newton BFGS. Click anywhere on the canvas to seed initial coordinates $(x_0, y_0)$:

::: canvas-walker landscape=rosenbrock algorithms=gd,armijo,newton,bfgs,momentum
:::

## 3. Constraint Handling: Barrier vs. Penalty

When inequality constraints $g(x) \\le 0$ are imposed, we relax the constrained objective via either Quadratic Penalties or Logarithmic Barriers:

$$P(x; \\mu) = f(x) + \\frac{{\\mu}}{{2}} \\max(0, g(x))^2, \\quad \\mu \\to \\infty$$

$$B(x; \\mu) = f(x) - \\mu \\ln(-g(x)), \\quad \\mu \\to 0^+$$

::: barrier-vs-penalty
:::

## 4. Algorithmic Selection Guide

::: decision-ladder
:::
"""

    (target_dir / "plot_optimization.py").write_text(sample_plot_py, encoding="utf-8")
    md_file.write_text(content, encoding="utf-8")
    (target_dir / ".gitignore").write_text("dist/\n__pycache__/\n*.html\n", encoding="utf-8")

    ui.success(f"Scaffolded new {template_type} project in '{name}/'")
    print(f"\n  \033[1;36mcd\033[0m {name}")
    print(f"  \033[1;36mlantern serve\033[0m {md_file.name}\n")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    """Compile Markdown into a self-contained HTML document."""
    target = args.file
    if not target:
        target_path = find_default_target()
        if not target_path:
            ui.error("No markdown document specified and none found in current directory.")
            return 1
    else:
        target_path = Path(target).resolve()

    if not target_path.exists():
        ui.error(f"File not found: {target_path}")
        return 1

    compiler = LanternCompiler()
    template_name = args.template or "explainer"
    standalone = bool(args.standalone)

    out_dest = args.output
    if not out_dest:
        out_dest = Path.cwd() / "dist" / f"{target_path.stem}.html"
    else:
        out_p = Path(out_dest)
        if out_p.is_dir() or str(out_dest).endswith(("/", "\\")):
            out_dest = out_p / f"{target_path.stem}.html"

    ui.info(f"Compiling \033[1m{target_path.name}\033[0m (template: {template_name}, standalone: {standalone})")
    try:
        out_file = compiler.compile_file(
            input_path=target_path,
            output_path=out_dest,
            template_name=template_name,
            standalone=standalone,
        )
        size_kb = out_file.stat().st_size / 1024.0
        ui.success(f"Built \033[1m{out_file.relative_to(Path.cwd()) if out_file.is_relative_to(Path.cwd()) else out_file}\033[0m ({size_kb:.1f} KB)")
        return 0
    except Exception as exc:
        ui.error(f"Compilation failed: {exc}")
        return 1


def cmd_serve(args: argparse.Namespace) -> int:
    """Spins up dev server with SSE live browser synchronization."""
    target = args.file
    if not target:
        target_path = find_default_target()
        if not target_path:
            ui.error("No markdown document specified and none found in current directory.")
            return 1
    else:
        target_path = Path(target).resolve()

    if not target_path.exists():
        ui.error(f"File not found: {target_path}")
        return 1

    port = int(args.port or 8080)
    host = args.host or "127.0.0.1"
    template_name = args.template or "explainer"
    no_open = bool(args.no_open)

    server = LanternDevServer(
        target_file=target_path,
        port=port,
        host=host,
        template_name=template_name,
    )

    url = f"http://{server.host}:{server.port}"
    lines = [
        f"URL:          \033[1;36m{url}\033[0m",
        f"Target:       \033[1m{target_path.name}\033[0m",
        f"Template:     {template_name}",
        f"Live Reload:  \033[32mActive (SSE /_lantern/events)\033[0m",
        f"Watching:     {target_path.parent}",
        "",
        "\033[2mPress Ctrl+C to stop dev server\033[0m",
    ]
    render_panel(title="🏮 Lantern Live Dev Server", lines=lines, border_color="1;36")

    try:
        server.start(open_browser=not no_open)
    except KeyboardInterrupt:
        print("\nDev server stopped.")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Display system status dashboard, engine availability, and active templates."""
    # Check Barograph availability
    barograph_status = "\033[31m✘ Not installed\033[0m"
    try:
        import barograph  # type: ignore

        baro_ver = getattr(barograph, "__version__", "available")
        barograph_status = f"\033[32m✓ In-process available (v{baro_ver})\033[0m"
    except ImportError:
        import shutil
        if shutil.which("barograph"):
            barograph_status = "\033[33m✓ CLI available in PATH (subprocess mode)\033[0m"

    # Check Prism availability
    prism_status = "\033[32m✓ Loaded\033[0m" if "prism" in sys.modules else "\033[33mANSI Fallback\033[0m"

    compiler = LanternCompiler()
    templates = [p.stem.replace(".html", "") for p in compiler.template_dir.glob("*.html.j2") if not p.name.startswith("base")]

    lines = [
        f"Lantern:       \033[1;36mv{__version__}\033[0m ({Path(__file__).parent})",
        f"Python:        {platform.python_version()} ({sys.executable})",
        f"Platform:      {platform.system()} {platform.machine()}",
        "",
        "\033[1mEngines & Integrations:\033[0m",
        f"  • Barograph:   {barograph_status}",
        f"  • Prism UI:    {prism_status}",
        f"  • KaTeX Math:  \033[32m✓ Bundled local\033[0m",
        f"  • Markdown:    \033[32m✓ Directives enabled\033[0m [plot, walker, barrier, decision, callout]",
        "",
        "\033[1mAvailable Templates:\033[0m",
    ]
    for tmpl in templates:
        lines.append(f"  • \033[1m{tmpl}\033[0m")

    target = find_default_target()
    if target:
        lines.extend(["", f"\033[1mActive Document:\033[0m {target.name} ({target.parent})"])

    render_panel(title="🏮 Lantern Status Dashboard", lines=lines, border_color="1;36")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """List available templates and detected markdown documents."""
    compiler = LanternCompiler()
    templates = [p.stem.replace(".html", "") for p in compiler.template_dir.glob("*.html.j2") if not p.name.startswith("base")]

    print(f"\n{ui.badge()} {ui.bold('Templates & Workspaces')}")
    print(f"\n\033[1mTemplates:\033[0m")
    for t in templates:
        print(f"  • {t}")

    mds = list(Path.cwd().glob("*.md"))
    print(f"\n\033[1mDocuments in {Path.cwd().name}/:\033[0m")
    if mds:
        for m in sorted(mds):
            print(f"  • {m.name}")
    else:
        print("  (No .md documents found)")
    print()
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        prog="lantern",
        description="Frost's Interactive Explainer and Simulation Dashboard Compiler",
    )
    parser.add_argument("-v", "--version", action="version", version=f"lantern {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Lantern commands")

    # new
    p_new = subparsers.add_parser("new", help="Scaffold a new explainer or simulation workspace")
    p_new.add_argument("name", help="Workspace / project directory name")
    p_new.add_argument("--template", choices=["explainer", "dashboard"], default="explainer", help="Starter template type")

    # build
    p_build = subparsers.add_parser("build", help="Compile Markdown into an optimized HTML document")
    p_build.add_argument("file", nargs="?", default="", help="Input markdown document (defaults to explainer.md / dashboard.md)")
    p_build.add_argument("-o", "--output", default="", help="Output HTML file or directory (default: dist/<name>.html)")
    p_build.add_argument("--standalone", action="store_true", help="Inline all CSS, KaTeX, and JS into a single standalone HTML file")
    p_build.add_argument("--template", choices=["explainer", "dashboard"], default="", help="Layout template override")

    # serve
    p_serve = subparsers.add_parser("serve", help="Spin up local live-reloading dev server with SSE browser sync")
    p_serve.add_argument("file", nargs="?", default="", help="Markdown document to watch and serve")
    p_serve.add_argument("-p", "--port", type=int, default=8080, help="HTTP port (default: 8080)")
    p_serve.add_argument("--host", default="127.0.0.1", help="HTTP host (default: 127.0.0.1)")
    p_serve.add_argument("--no-open", action="store_true", help="Do not automatically open browser on launch")
    p_serve.add_argument("--template", choices=["explainer", "dashboard"], default="", help="Template override")

    # status
    subparsers.add_parser("status", help="Display Prism terminal dashboard of active engines and templates")

    # list
    subparsers.add_parser("list", help="List available templates and documents")

    args = parser.parse_args(argv)

    if not args.command:
        # Default to status if no arguments provided
        return cmd_status(args)

    if args.command == "new":
        return cmd_new(args)
    elif args.command == "build":
        return cmd_build(args)
    elif args.command == "serve":
        return cmd_serve(args)
    elif args.command == "status":
        return cmd_status(args)
    elif args.command == "list":
        return cmd_list(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
