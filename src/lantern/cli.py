"""CLI commands, router, and Prism interactive interface for Lantern."""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Any, Sequence

from lantern import __version__
from lantern.compiler import LanternCompiler
from lantern.server import LanternDevServer
from lantern.ui import (
    add_color_args,
    handle_color_args,
    prompt_input,
    render_panel,
    select_menu,
    ui,
)


def get_usage() -> str:
    """Returns the Prism-styled help and usage guide matching Snowpack & Borealis, or compact agent guide."""
    if ui.is_agent:
        return f"""Lantern v{__version__} - Frost Explainer & Simulation Dashboard Compiler
Usage: lantern [command] [file.md] [options]

Commands:
  new <name> [-t explainer|dashboard|optimization]
  build [file] [-o out.html] [--standalone] [-t template]
  export [file] [-o dist/] [--format static|jinja] [-t template]
  serve [file] [-p port] [--host host] [--no-open]
  status [--json]
  list [--json]

Options:
  --agent, -A            Compact machine/agent friendly output
  --json                 Structured JSON output
  -o, --output PATH      Output destination file or directory
  -t, --template NAME    Template name (default: explainer)
  --standalone           Inline all CSS, KaTeX, and JS into single file
  -p, --port PORT        Dev server port (default: 8080)
  --no-open              Do not auto-open browser
  -h, --help             Show this help message
  -v, --version          Show version number
"""

    return f"""{ui.badge()} {ui.bold("Frost's Interactive Explainer & Simulation Dashboard Compiler")}

{ui.blue("Usage:")}
  lantern                               Open interactive dashboard & quick actions
  lantern [file] [options]              Compile Markdown into standalone HTML
  lantern build [file] [options]        Explicit compilation command
  lantern export [file] [options]       Export deployable static bundle or Jinja2 server project
  lantern serve [file] [options]        Spin up live-reloading dev server with SSE browser sync
  lantern new <name> [options]          Scaffold a new explainer or simulation workspace
  lantern status                        Display Prism terminal dashboard of active engines
  lantern list                          List available templates and documents

{ui.blue("Commands:")}
  new <name>             Scaffold a starter explainer, dashboard, or optimization lab
  build [file]           Compile Markdown into an optimized HTML document
  export [file]          Export static bundle or standalone Jinja2 web application project
  serve [file]           Spin up ephemeral HTTP dev server with browser live-reloading
  status                 Display Prism telemetry dashboard & engine availability
  list                   List available templates and detected markdown documents

{ui.blue("Options:")}
  -o, --output PATH      Specify output HTML filename or export directory
  -t, --template NAME    Layout template: 'explainer' (default), 'dashboard', or 'optimization'
  --format FORMAT        Export format for 'export': 'static' (default) or 'jinja'
  --standalone           Inline all CSS, KaTeX math, and JavaScript into a single HTML file
  -p, --port PORT        Dev server HTTP port (default: 8080)
  --host HOST            Dev server host (default: 127.0.0.1)
  --no-open              Do not automatically open browser on launch
  --agent, -A            Compact machine/agent friendly output mode
  --json                 Output structured JSON payloads for agent/MCP tooling
  --color MODE           Color output mode: auto, always, never (default: auto)
  --no-color             Disable colored output
  -h, --help             Show this help message and exit
  -V, -v, --version      Show version information and exit

{ui.blue("Directives Ecosystem:")}
  • {ui.bold("Layout:")}    ::: grid, ::: card, ::: stepper, ::: curtain
  • {ui.bold("Controls:")}  ::: slider, ::: switch, ::: segments, ::: select, ::: player
  • {ui.bold("Content:")}   ::: plot (with lightbox modal), ::: metrics, ::: tabs,
                  ::: accordion, ::: comparison, ::: callout, [?term: hint]

{ui.blue("Examples:")}
  lantern                               # Interactive dashboard & quick action menu
  lantern explainer.md                  # Compile explainer.md -> dist/explainer.html
  lantern build explainer.md --standalone # Self-contained HTML with inlined assets
  lantern export explainer.md           # Self-contained static bundle with Nginx/Caddy config
  lantern export explainer.md --format jinja # Standalone Python Jinja2 project with Dockerfile
  lantern serve explainer.md            # Live-reloading server at http://127.0.0.1:8080
  lantern new convex-lab --template optimization # Scaffold domain optimization lab
  lantern status --agent                # Machine-friendly status output
"""


def discover_documents(cwd: Path | None = None) -> list[Path]:
    """Discovers all Markdown documents in target directory, sorting preferred names first."""
    base = cwd or Path.cwd()
    if not base.exists():
        return []
    candidates = list(base.glob("*.md"))
    preferred = ("explainer.md", "dashboard.md", "index.md", "README.md")

    def sort_key(p: Path) -> tuple[int, str]:
        lower = p.name.lower()
        if lower in preferred:
            return (preferred.index(lower), lower)
        return (len(preferred), lower)

    return sorted(candidates, key=sort_key)


def find_default_target(cwd: Path | None = None) -> Path | None:
    """Finds primary target markdown file in current directory."""
    docs = discover_documents(cwd)
    return docs[0] if docs else None


def cmd_new(args: argparse.Namespace) -> int:
    """Scaffold a new explainer, simulation dashboard, or domain lab workspace."""
    name: str = args.name
    template_type: str = (args.template or "explainer").lower()
    target_dir = Path.cwd() / name

    if target_dir.exists():
        ui.error(f"Directory '{name}' already exists.")
        return 1

    target_dir.mkdir(parents=True, exist_ok=True)
    compiler = LanternCompiler()

    if template_type == "optimization":
        opt_template_dir = compiler.template_dir / "optimization"
        if opt_template_dir.exists():
            shutil.copytree(opt_template_dir, target_dir, dirs_exist_ok=True)
            (target_dir / ".gitignore").write_text(
                "dist/\n__pycache__/\n*.html\n", encoding="utf-8"
            )
            ui.success(f"Scaffolded new optimization lab workspace in '{name}/'")
            print(f"\n  {ui.bold_cyan('cd')} {name}")
            print(f"  {ui.bold_cyan('lantern serve')} explainer.md\n")
            return 0

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
title: "{name.title()} Simulation Dashboard"
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
title: "{name.title()} Interactive Explainer"
subtitle: "A Mathematical Deep-Dive with Live Visualizations"
author: "Frost Research Group"
template: explainer
---

# Introduction

Welcome to **{name.title()}**. This document is an interactive scientific explainer compiled with `Lantern`.

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

    ui.success(f"Scaffolded new {template_type} project in '{name}/'")
    print(f"\n  {ui.bold_cyan('cd')} {name}")
    print(f"  {ui.bold_cyan('lantern serve')} {md_file.name}\n")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    """Compile Markdown into a self-contained HTML document."""
    target = getattr(args, "file", "")
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

    # Large Markdown safeguard & telemetry
    size_bytes = target_path.stat().st_size
    if size_bytes > 2 * 1024 * 1024:
        ui.info(
            f"Large document detected ({size_bytes / (1024 * 1024):.1f} MB); activating optimized streaming parser..."
        )

    compiler = LanternCompiler()
    template_name = getattr(args, "template", None) or "explainer"
    standalone = bool(getattr(args, "standalone", True))

    out_dest = getattr(args, "output", "")
    if not out_dest:
        out_dest = Path.cwd() / "dist" / f"{target_path.stem}.html"
    else:
        out_p = Path(out_dest)
        if out_p.is_dir() or str(out_dest).endswith(("/", "\\")):
            out_dest = out_p / f"{target_path.stem}.html"

    ui.action(
        f"Compiling {ui.bold(target_path.name)} (template: {template_name}, standalone: {standalone})...",
        symbol="🏮",
    )
    try:
        out_file = compiler.compile_file(
            input_path=target_path,
            output_path=out_dest,
            template_name=template_name,
            standalone=standalone,
        )
        size_kb = out_file.stat().st_size / 1024.0
        rel = (
            out_file.relative_to(Path.cwd())
            if out_file.is_relative_to(Path.cwd())
            else out_file
        )

        if ui.is_json:
            import json

            print(
                json.dumps(
                    {
                        "status": "ok",
                        "target": str(target_path),
                        "output": str(out_file),
                        "size_bytes": out_file.stat().st_size,
                        "template": template_name,
                        "standalone": standalone,
                    }
                )
            )
            return 0

        ui.success(f"Built {ui.bold(str(rel))} ({size_kb:.1f} KB)")
        return 0
    except Exception as exc:
        ui.error(f"Compilation failed: {exc}")
        return 1


def cmd_export(args: argparse.Namespace) -> int:
    """Export deployable static bundle or standalone Jinja2 server project."""
    target = getattr(args, "file", "")
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

    export_format = (getattr(args, "format", "static") or "static").lower()
    template_name = getattr(args, "template", "") or "explainer"
    output_dir = getattr(args, "output", "") or None

    compiler = LanternCompiler()

    ui.action(
        f"Exporting {ui.bold(target_path.name)} (format: {export_format}, template: {template_name})...",
        symbol="📦",
    )
    try:
        if export_format == "jinja":
            out_path = compiler.export_jinja(
                input_path=target_path,
                output_dir=output_dir,
                template_name=template_name,
            )
        else:
            out_path = compiler.export_static(
                input_path=target_path,
                output_dir=output_dir,
                template_name=template_name,
            )

        files = [str(p.relative_to(out_path)) for p in out_path.rglob("*") if p.is_file()]
        rel = (
            out_path.relative_to(Path.cwd())
            if out_path.is_relative_to(Path.cwd())
            else out_path
        )

        if ui.is_json:
            import json

            print(
                json.dumps(
                    {
                        "status": "ok",
                        "format": export_format,
                        "target": str(target_path),
                        "output_dir": str(out_path),
                        "file_count": len(files),
                        "files": files,
                    }
                )
            )
            return 0

        ui.success(f"Exported {export_format} bundle to {ui.bold(str(rel))} ({len(files)} files)")
        if not ui.is_agent:
            print(f"\n  {ui.dim('Deployment manual:')} {out_path}/README.md\n")
        return 0
    except Exception as exc:
        ui.error(f"Export failed: {exc}")
        return 1


def cmd_serve(args: argparse.Namespace) -> int:
    """Spins up dev server with SSE live browser synchronization."""
    target = getattr(args, "file", "")
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

    port = int(getattr(args, "port", None) or 8080)
    host = getattr(args, "host", None) or "127.0.0.1"
    template_name = getattr(args, "template", None) or "explainer"
    no_open = bool(getattr(args, "no_open", False))

    server = LanternDevServer(
        target_file=target_path,
        port=port,
        host=host,
        template_name=template_name,
    )

    url = f"http://{server.host}:{server.port}"
    lines = [
        f"URL:          {ui.bold_cyan(url)}",
        f"Target:       {ui.bold(target_path.name)}",
        f"Template:     {template_name}",
        f"Live Reload:  {ui.green('Active (SSE /_lantern/events)')}",
        f"Watching:     {target_path.parent}",
        "",
        ui.yellow("⚠️  Ephemeral local dev server only. Not intended for production hosting."),
        ui.dim("   For production hosting, compile with 'lantern export'."),
        "",
        f"Controls:     {ui.bold('[q]')} or {ui.bold('[Ctrl+C]')} to stop  |  {ui.bold('[r]')} reload  |  {ui.bold('[o]')} open",
    ]
    ui.panel("🏮 Lantern Live Dev Server", lines, border_color="1;36")

    try:
        server.start(open_browser=not no_open)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        print(f"\n{ui.badge()} Dev server stopped.")
    return 0


def cmd_status(args: argparse.Namespace | None = None) -> int:
    """Display system status dashboard, engine availability, and active templates."""
    baro_mode = "none"
    barograph_status = ui.red("✘ Not installed")
    try:
        import barograph  # type: ignore

        baro_ver = getattr(barograph, "__version__", "available")
        barograph_status = ui.green(f"✓ In-process available (v{baro_ver})")
        baro_mode = f"in-process (v{baro_ver})"
    except ImportError:
        import shutil

        if shutil.which("barograph"):
            barograph_status = ui.yellow("✓ CLI available in PATH (subprocess mode)")
            baro_mode = "cli"

    prism_active = False
    try:
        import prism  # type: ignore

        prism_ver = getattr(prism, "__version__", "loaded")
        prism_status = ui.green(f"✓ Native Prism active (v{prism_ver})")
        prism_active = True
    except ImportError:
        prism_status = ui.yellow("ANSI Fallback")

    compiler = LanternCompiler()
    templates = [
        p.stem.replace(".html", "")
        for p in compiler.template_dir.glob("*.html.j2")
        if not p.name.startswith("base")
    ]
    if (compiler.template_dir / "optimization").exists():
        templates.append("optimization")

    docs = discover_documents()

    if ui.is_json:
        import json

        print(
            json.dumps(
                {
                    "app": "lantern",
                    "version": __version__,
                    "python": platform.python_version(),
                    "platform": f"{platform.system()} {platform.machine()}",
                    "barograph": baro_mode,
                    "prism": prism_active,
                    "katex": True,
                    "templates": templates,
                    "active_document": docs[0].name if docs else None,
                    "documents": [d.name for d in docs],
                }
            )
        )
        return 0

    lines = [
        f"Lantern:       {ui.bold_cyan(f'v{__version__}')} ({Path(__file__).parent})",
        f"Python:        {platform.python_version()} ({sys.executable})",
        f"Platform:      {platform.system()} {platform.machine()}",
        "",
        ui.bold("Engines & Integrations:"),
        f"  • Barograph:   {barograph_status}",
        f"  • Prism UI:    {prism_status}",
        f"  • KaTeX Math:  {ui.green('✓ Bundled local')}",
        f"  • Directives:  {ui.green('✓ Enabled (3 Families)')}",
        "    - Layout:    grid, card, stepper, curtain",
        "    - Controls:  slider, switch, segments, select, player",
        "    - Content:   plot, metrics, tabs, accordion, comparison, callout",
        "",
        ui.bold("Available Templates:"),
    ]
    for tmpl in templates:
        lines.append(f"  • {ui.bold(tmpl)}")

    if docs:
        lines.extend(["", f"{ui.bold('Active Document:')} {docs[0].name} ({docs[0].parent})"])
        if len(docs) > 1:
            lines.append(f"{ui.dim('Workspace Files:')} {', '.join(d.name for d in docs)}")

    ui.panel("🏮 LANTERN STATUS DASHBOARD", lines, border_color="1;36")
    return 0


def cmd_list(args: argparse.Namespace | None = None) -> int:
    """List available templates and detected markdown documents."""
    compiler = LanternCompiler()
    templates = [
        p.stem.replace(".html", "")
        for p in compiler.template_dir.glob("*.html.j2")
        if not p.name.startswith("base")
    ]
    if (compiler.template_dir / "optimization").exists():
        templates.append("optimization")

    docs = discover_documents()

    if ui.is_json:
        import json

        print(
            json.dumps(
                {
                    "templates": templates,
                    "documents": [
                        {"name": d.name, "path": str(d), "size_bytes": d.stat().st_size}
                        for d in docs
                    ],
                }
            )
        )
        return 0

    if ui.is_agent:
        print("Templates:")
        for t in templates:
            print(f"  {t}")
        print("Documents:")
        for d in docs:
            print(f"  {d.name} ({d.stat().st_size} bytes)")
        return 0

    print(f"\n{ui.badge()} {ui.bold('Templates & Workspaces')}")
    print(f"\n{ui.bold('Templates:')}")
    for t in templates:
        print(f"  • {t}")

    print(f"\n{ui.bold(f'Documents in {Path.cwd().name}/:')}")
    if docs:
        for m in docs:
            size_kb = m.stat().st_size / 1024.0
            print(f"  • {ui.bold_cyan(m.name)} {ui.dim(f'({size_kb:.1f} KB)')}")
    else:
        print(f"  {ui.dim('(No .md documents found)')}")
    print()
    return 0


def run_interactive_hub(docs: list[Path]) -> int:
    """Provides interactive quick actions menu when Lantern is run with no arguments."""
    actions: list[tuple[str, str, str]] = []

    if docs:
        first = docs[0]
        actions.append(
            (
                "serve_first",
                f"Serve & live-reload '{first.name}'",
                "Spins up dev server with SSE live browser sync",
            )
        )
        actions.append(
            (
                "build_first",
                f"Compile '{first.name}' to standalone HTML",
                "Inlines CSS, KaTeX math, and JavaScript into self-contained file",
            )
        )
        actions.append(
            (
                "export_first",
                f"Export '{first.name}' bundle",
                "Deployable static bundle or standalone Jinja2 server project",
            )
        )
        if len(docs) > 1:
            actions.append(
                (
                    "select_serve",
                    "Pick document to live-serve...",
                    f"{len(docs)} markdown files discovered",
                )
            )
            actions.append(
                (
                    "select_build",
                    "Pick document to compile...",
                    f"{len(docs)} markdown files discovered",
                )
            )
    else:
        actions.append(
            (
                "build_custom",
                "Compile a markdown document...",
                "Specify a custom file path to compile",
            )
        )
        actions.append(
            (
                "serve_custom",
                "Serve & live-reload a document...",
                "Live reload a specific document path",
            )
        )

    actions.append(
        (
            "new",
            "Scaffold new explainer or simulation workspace",
            "Generate explainer, dashboard, or optimization lab project",
        )
    )
    actions.append(
        (
            "list",
            "List available templates & documents",
            "Display installed templates and workspace files",
        )
    )
    actions.append(("exit", "Exit", "Close Lantern"))

    choice = ui.select("Lantern Quick Actions:", actions)

    if choice == "exit" or not choice:
        return 0

    if choice == "serve_first" and docs:
        args = argparse.Namespace(file=str(docs[0]), port=8080, host="127.0.0.1", template="", no_open=False)
        return cmd_serve(args)

    if choice == "build_first" and docs:
        args = argparse.Namespace(file=str(docs[0]), output="", standalone=True, template="")
        return cmd_build(args)

    if choice == "export_first" and docs:
        fmt = ui.select(
            "Select export format:",
            [
                ("static", "Static Web Bundle", "HTML + CSS/JS/KaTeX ready for Caddy/Nginx/Cloudflare"),
                ("jinja", "Jinja2 Server Project", "app.py + templates + Dockerfile"),
            ],
        )
        if not fmt:
            return 0
        args = argparse.Namespace(file=str(docs[0]), output="", format=fmt, template="")
        return cmd_export(args)

    if choice == "select_serve" and docs:
        options = [
            (str(d), f"📄 {d.name}", f"{d.stat().st_size:,} bytes") for d in docs
        ]
        target = ui.select("Select document to serve:", options)
        if not target:
            return 0
        args = argparse.Namespace(file=target, port=8080, host="127.0.0.1", template="", no_open=False)
        return cmd_serve(args)

    if choice == "select_build" and docs:
        options = [
            (str(d), f"📄 {d.name}", f"{d.stat().st_size:,} bytes") for d in docs
        ]
        target = ui.select("Select document to compile:", options)
        if not target:
            return 0
        args = argparse.Namespace(file=target, output="", standalone=True, template="")
        return cmd_build(args)

    if choice == "build_custom":
        target = ui.prompt("Document path to compile (.md)", default="explainer.md")
        if not Path(target).exists():
            ui.error(f"File not found: '{target}'")
            return 1
        args = argparse.Namespace(file=target, output="", standalone=True, template="")
        return cmd_build(args)

    if choice == "serve_custom":
        target = ui.prompt("Document path to serve (.md)", default="explainer.md")
        if not Path(target).exists():
            ui.error(f"File not found: '{target}'")
            return 1
        args = argparse.Namespace(file=target, port=8080, host="127.0.0.1", template="", no_open=False)
        return cmd_serve(args)

    if choice == "new":
        tmpl = ui.select(
            "Select starter template:",
            [
                ("explainer", "Scientific Explainer", "Narrative deep-dive with 3D plot and parameter lab"),
                ("dashboard", "Simulation Dashboard", "Multi-method simulation deck with control center"),
                ("optimization", "Domain Optimization Lab", "Canvas descent walker, barrier boundary lab, Rosenbrock surface"),
            ],
        )
        if not tmpl:
            return 0
        name = ui.prompt("Project / workspace directory name", default=f"my_{tmpl}")
        args = argparse.Namespace(name=name, template=tmpl)
        return cmd_new(args)

    if choice == "list":
        return cmd_list(None)

    return 0


def _build_parser() -> argparse.ArgumentParser:
    """Constructs argument parser for subcommands."""
    parser = argparse.ArgumentParser(
        prog="lantern",
        add_help=False,
    )
    parser.add_argument("-v", "-V", "--version", action="store_true", help="Show version")
    parser.add_argument("-h", "--help", action="store_true", help="Show help")
    parser.add_argument("-A", "--agent", action="store_true", help="Compact agent-friendly output mode")
    parser.add_argument("--json", action="store_true", help="Structured JSON output for MCP/agents")
    add_color_args(parser)

    subparsers = parser.add_subparsers(dest="command")

    # new
    p_new = subparsers.add_parser("new", add_help=False)
    p_new.add_argument("name", nargs="?", default="", help="Workspace directory name")
    p_new.add_argument("--template", "-t", choices=["explainer", "dashboard", "optimization"], default="explainer")
    p_new.add_argument("-A", "--agent", action="store_true")
    p_new.add_argument("--json", action="store_true")
    p_new.add_argument("-h", "--help", action="store_true")

    # build
    p_build = subparsers.add_parser("build", add_help=False)
    p_build.add_argument("file", nargs="?", default="", help="Input markdown document")
    p_build.add_argument("-o", "--output", default="", help="Output HTML destination")
    p_build.add_argument("--standalone", action="store_true", default=True, help="Inline all CSS, KaTeX, and JS")
    p_build.add_argument("--template", "-t", default="", help="Layout template override")
    p_build.add_argument("-A", "--agent", action="store_true")
    p_build.add_argument("--json", action="store_true")
    p_build.add_argument("-h", "--help", action="store_true")

    # export
    p_export = subparsers.add_parser("export", add_help=False)
    p_export.add_argument("file", nargs="?", default="", help="Input markdown document to export")
    p_export.add_argument("-o", "--output", default="", help="Output directory destination")
    p_export.add_argument("--format", choices=["static", "jinja"], default="static", help="Export bundle format")
    p_export.add_argument("--template", "-t", default="", help="Layout template override")
    p_export.add_argument("-A", "--agent", action="store_true")
    p_export.add_argument("--json", action="store_true")
    p_export.add_argument("-h", "--help", action="store_true")

    # serve
    p_serve = subparsers.add_parser("serve", add_help=False)
    p_serve.add_argument("file", nargs="?", default="", help="Markdown document to watch and serve")
    p_serve.add_argument("-p", "--port", type=int, default=8080, help="HTTP port")
    p_serve.add_argument("--host", default="127.0.0.1", help="HTTP host")
    p_serve.add_argument("--no-open", action="store_true", help="Do not open browser")
    p_serve.add_argument("--template", "-t", default="", help="Template override")
    p_serve.add_argument("-A", "--agent", action="store_true")
    p_serve.add_argument("--json", action="store_true")
    p_serve.add_argument("-h", "--help", action="store_true")

    # status
    p_status = subparsers.add_parser("status", add_help=False)
    p_status.add_argument("-A", "--agent", action="store_true")
    p_status.add_argument("--json", action="store_true")
    p_status.add_argument("-h", "--help", action="store_true")

    # list
    p_list = subparsers.add_parser("list", add_help=False)
    p_list.add_argument("-A", "--agent", action="store_true")
    p_list.add_argument("--json", action="store_true")
    p_list.add_argument("-h", "--help", action="store_true")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Main CLI entrypoint for Lantern."""
    raw_args = list(argv) if argv is not None else sys.argv[1:]
    handle_color_args(raw_args)

    # Agent mode detection (CLI flags & environment variables)
    agent_flag = any(a in ("--agent", "-A") for a in raw_args)
    json_flag = any(a in ("--json",) for a in raw_args)
    if agent_flag or json_flag or ui.check_agent_env():
        ui.set_agent_mode(agent=True, json_output=json_flag)

    # Global help intercept
    if any(a in ("-h", "--help", "help") for a in raw_args):
        print(get_usage())
        return 0

    # Global version intercept
    if any(a in ("-V", "-v", "--version", "version") for a in raw_args) and len(raw_args) == 1:
        if ui.is_json:
            import json

            print(json.dumps({"app": "lantern", "version": __version__}))
            return 0
        if ui.is_agent:
            print(f"lantern {__version__}")
            return 0
        print(f"{ui.badge()} {ui.bold(f'v{__version__}')}")
        return 0

    # When run without arguments: display dashboard and interactive hub
    if not raw_args:
        cmd_status()
        docs = discover_documents()
        if sys.stdin.isatty() and not ui.is_agent:
            return run_interactive_hub(docs)
        return 0

    cmd = raw_args[0]

    # Handle direct document compilation without explicit 'build' keyword
    # e.g., 'lantern explainer.md' or 'lantern explainer.md --standalone'
    known_commands = ("new", "build", "export", "serve", "status", "list")
    if cmd not in known_commands and not cmd.startswith("-"):
        p = Path(cmd)
        if p.suffix == ".md" or p.exists():
            build_raw = ["build"] + raw_args
            return main(build_raw)

    parser = _build_parser()
    args, _ = parser.parse_known_args(raw_args)

    if getattr(args, "agent", False) or getattr(args, "json", False):
        ui.set_agent_mode(agent=True, json_output=getattr(args, "json", False))

    if getattr(args, "help", False):
        print(get_usage())
        return 0

    if getattr(args, "version", False):
        if ui.is_json:
            import json

            print(json.dumps({"app": "lantern", "version": __version__}))
            return 0
        if ui.is_agent:
            print(f"lantern {__version__}")
            return 0
        print(f"{ui.badge()} {ui.bold(f'v{__version__}')}")
        return 0

    if args.command == "new":
        if not args.name:
            if sys.stdin.isatty() and not ui.is_agent:
                args.name = ui.prompt("Workspace directory name", default="my_explainer")
            else:
                ui.error("Missing required argument: <name>")
                return 1
        return cmd_new(args)

    elif args.command == "build":
        return cmd_build(args)

    elif args.command == "export":
        return cmd_export(args)

    elif args.command == "serve":
        return cmd_serve(args)

    elif args.command == "status":
        return cmd_status(args)

    elif args.command == "list":
        return cmd_list(args)

    else:
        print(get_usage())
        return 1


if __name__ == "__main__":
    sys.exit(main())
