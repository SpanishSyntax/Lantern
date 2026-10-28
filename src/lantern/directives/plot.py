"""Plot directive processor for Lantern (::: plot script.py ...)."""

from __future__ import annotations

import html
import io
import os
import re
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as etree
from markdown.blockprocessors import BlockProcessor


class PlotBlockProcessor(BlockProcessor):
    """Processes ::: plot <script.py> [backend=plotly|svg] [height=500px] blocks."""

    START_RE = re.compile(
        r"^:::\s*plot\s+(?P<script>[^\s]+)(?:\s+(?P<args>.*))?$",
        re.IGNORECASE,
    )
    END_RE = re.compile(r"^:::\s*$")

    def __init__(self, parser: Any, compiler: Any = None, base_dir: Path | None = None) -> None:
        super().__init__(parser)
        self.compiler = compiler
        self.base_dir = Path(base_dir or os.getcwd()).resolve()

    def test(self, parent: etree.Element, block: str) -> bool:
        lines = block.strip().splitlines()
        if not lines:
            return False
        return bool(self.START_RE.match(lines[0]))

    def run(self, parent: etree.Element, blocks: list[str]) -> bool:
        if not blocks:
            return False
        lines = blocks[0].strip().splitlines()
        if not lines:
            return False
        match = self.START_RE.match(lines[0])
        if not match:
            return False

        script_name = match.group("script")
        args_str = match.group("args") or ""

        # Parse options
        backend = "plotly"
        height = "520px"

        b_match = re.search(r"backend=(plotly|svg|matplotlib|seaborn)", args_str, re.IGNORECASE)
        if b_match:
            backend = b_match.group(1).lower()

        h_match = re.search(r"height=([0-9]+(?:px|vh|%|rem))", args_str, re.IGNORECASE)
        if h_match:
            height = h_match.group(1)

        # Consume blocks if multiline directive
        blocks.pop(0)
        # Check if closed on subsequent block
        while blocks:
            blk = blocks[0].strip()
            if self.END_RE.match(blk):
                blocks.pop(0)
                break
            # If not closing :::, break to let other blocks parse
            break

        # Resolve script path
        script_path = (self.base_dir / script_name).resolve()
        if not script_path.exists():
            # Check relative to cwd
            cwd_path = Path(script_name).resolve()
            if cwd_path.exists():
                script_path = cwd_path

        # Register script with compiler for live watch
        if self.compiler is not None:
            self.compiler.register_watched_script(script_path)

        # Execute and render figure
        plot_html, has_plotly = self._render_plot(script_path, backend, height)
        if has_plotly and self.compiler is not None:
            self.compiler.has_plotly = True

        # Store HTML in markdown stash to prevent mangling
        placeholder = self.parser.md.htmlStash.store(plot_html)
        p = etree.SubElement(parent, "div")
        p.text = placeholder
        return True

    def _render_plot(self, script_path: Path, requested_backend: str, height: str) -> tuple[str, bool]:
        """Execute script via Barograph (in-process or subprocess fallback) and return (html, has_plotly)."""
        if not script_path.exists():
            return (
                f'<div class="lantern-callout lantern-callout-danger">'
                f'<div class="lantern-callout-header"><span>✘</span><span>Plot Script Not Found</span></div>'
                f'<div class="lantern-callout-body"><p>Referenced script <code>{html.escape(script_path.name)}</code> was not found at <code>{html.escape(str(script_path))}</code>.</p></div>'
                f'</div>',
                False,
            )

        # 1. Attempt in-process execution via Barograph
        try:
            import barograph  # type: ignore

            if hasattr(barograph, "run_script"):
                res = barograph.run_script(script_path)
                fig = res.figure
                detected = getattr(res, "backend", "generic")
                return self._serialize_figure(fig, detected, requested_backend, height, script_path)
        except Exception:
            pass

        # 2. Attempt subprocess execution via Barograph CLI
        try:
            barograph_bin = "barograph"
            with tempfile.TemporaryDirectory() as tmpdir:
                fmt = "svg" if requested_backend == "svg" else "html"
                cmd = [barograph_bin, "build", str(script_path), "--format", fmt, "--out-dir", tmpdir]
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
                if proc.returncode == 0:
                    out_files = list(Path(tmpdir).glob(f"*.{fmt}"))
                    if out_files:
                        content = out_files[0].read_text(encoding="utf-8")
                        return self._wrap_raw_output(content, fmt, height, script_path)
        except Exception:
            pass

        # 3. Direct in-process execution fallback
        try:
            import runpy

            # Pre-set matplotlib non-interactive backend
            try:
                import matplotlib  # type: ignore
                matplotlib.use("Agg")
                import matplotlib.pyplot as plt  # type: ignore
                plt.close("all")
            except ImportError:
                plt = None

            cwd = os.getcwd()
            try:
                os.chdir(script_path.parent)
                sys.path.insert(0, str(script_path.parent))
                mod_globals = runpy.run_path(str(script_path))
            finally:
                os.chdir(cwd)
                if sys.path and sys.path[0] == str(script_path.parent):
                    sys.path.pop(0)

            # Search figure
            fig = None
            for attr in ("fig", "figure", "plot", "dashboard"):
                if attr in mod_globals:
                    val = mod_globals[attr]
                    if callable(val) and not hasattr(val, "savefig") and not hasattr(val, "to_html"):
                        try:
                            val = val()
                        except Exception:
                            pass
                    fig = val
                    break

            if fig is None and plt is not None:
                if plt.get_fignums():
                    fig = plt.gcf()

            if fig is not None:
                backend = "plotly" if hasattr(fig, "to_html") or hasattr(fig, "write_html") else "matplotlib"
                return self._serialize_figure(fig, backend, requested_backend, height, script_path)

            return (
                f'<div class="lantern-callout lantern-callout-warning">'
                f'<div class="lantern-callout-header"><span>⚠</span><span>No Figure Detected</span></div>'
                f'<div class="lantern-callout-body"><p>Script <code>{html.escape(script_path.name)}</code> executed without exporting a <code>fig</code> object or Matplotlib plot.</p></div>'
                f'</div>',
                False,
            )
        except Exception as exc:
            tb = traceback.format_exc()
            return (
                f'<div class="lantern-callout lantern-callout-danger">'
                f'<div class="lantern-callout-header"><span>✘</span><span>Plot Execution Error ({html.escape(script_path.name)})</span></div>'
                f'<div class="lantern-callout-body"><pre><code>{html.escape(tb)}</code></pre></div>'
                f'</div>',
                False,
            )

    def _serialize_figure(
        self, fig: Any, detected_backend: str, requested_backend: str, height: str, script_path: Path
    ) -> tuple[str, bool]:
        """Convert a live Python figure object into HTML or SVG markup."""
        # Plotly
        if (requested_backend == "plotly" or detected_backend == "plotly") and (hasattr(fig, "to_html") or hasattr(fig, "write_html")):
            if hasattr(fig, "to_html"):
                inner = fig.to_html(include_plotlyjs=False, full_html=False, default_height=height)
            else:
                buf = io.StringIO()
                fig.write_html(buf, include_plotlyjs=False, full_html=False, default_height=height)
                inner = buf.getvalue()

            wrapped = f"""
<div class="lantern-plot-wrapper">
  <div class="lantern-plot-header">
    <div class="lantern-plot-title">
      <span class="lantern-badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; border-color: rgba(56, 189, 248, 0.3); margin-bottom: 0;">Plotly Interactive</span>
      <span>{html.escape(script_path.name)}</span>
    </div>
  </div>
  <div class="lantern-plot-content" style="min-height: {height};">
    {inner}
  </div>
</div>
"""
            return wrapped, True

        # SVG (Matplotlib / Seaborn)
        if hasattr(fig, "savefig"):
            buf = io.StringIO()
            fig.savefig(buf, format="svg", bbox_inches="tight", transparent=True)
            svg_text = buf.getvalue()
            # Strip XML header if present
            svg_text = re.sub(r"<\?xml.*?\?>", "", svg_text)
            svg_text = re.sub(r"<!DOCTYPE.*?>", "", svg_text)
            wrapped = f"""
<div class="lantern-plot-wrapper">
  <div class="lantern-plot-header">
    <div class="lantern-plot-title">
      <span class="lantern-badge" style="background: rgba(52, 211, 153, 0.15); color: #34d399; border-color: rgba(52, 211, 153, 0.3); margin-bottom: 0;">Vector SVG</span>
      <span>{html.escape(script_path.name)}</span>
    </div>
  </div>
  <div class="lantern-plot-content" style="min-height: {height}; padding: 1.5rem;">
    {svg_text}
  </div>
</div>
"""
            return wrapped, False

        # Raw string HTML / SVG
        if isinstance(fig, str):
            return self._wrap_raw_output(fig, "svg" if "<svg" in fig else "html", height, script_path)

        return (f"<p>Unhandled figure backend: {type(fig)}</p>", False)

    def _wrap_raw_output(self, content: str, fmt: str, height: str, script_path: Path) -> tuple[str, bool]:
        has_plotly = "plotly" in content.lower()
        badge_text = "Vector SVG" if fmt == "svg" else "Interactive Plot"
        badge_color = "#34d399" if fmt == "svg" else "#38bdf8"
        wrapped = f"""
<div class="lantern-plot-wrapper">
  <div class="lantern-plot-header">
    <div class="lantern-plot-title">
      <span class="lantern-badge" style="background: rgba(56, 189, 248, 0.15); color: {badge_color}; border-color: rgba(56, 189, 248, 0.3); margin-bottom: 0;">{badge_text}</span>
      <span>{html.escape(script_path.name)}</span>
    </div>
  </div>
  <div class="lantern-plot-content" style="min-height: {height}; padding: 1rem;">
    {content}
  </div>
</div>
"""
        return wrapped, has_plotly
