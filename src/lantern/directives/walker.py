"""Canvas Walker directive processor for Lantern (::: canvas-walker ...)."""

from __future__ import annotations

import html
import re
from typing import Any
import xml.etree.ElementTree as etree
from markdown.blockprocessors import BlockProcessor


class CanvasWalkerBlockProcessor(BlockProcessor):
    """Processes ::: canvas-walker [landscape=...] [algorithms=...] blocks."""

    START_RE = re.compile(
        r"^:::\s*canvas-walker(?:\s+(?P<args>.*))?$",
        re.IGNORECASE,
    )
    END_RE = re.compile(r"^:::\s*$")

    _counter = 0

    def __init__(self, parser: Any, compiler: Any = None) -> None:
        super().__init__(parser)
        self.compiler = compiler

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

        args_str = match.group("args") or ""

        # Parse parameters
        landscape = "rosenbrock"
        ls_match = re.search(r"landscape=(rosenbrock|ellipse|rastrigin|saddle)", args_str, re.IGNORECASE)
        if ls_match:
            landscape = ls_match.group(1).lower()

        algorithms = "gd,armijo,newton,bfgs,momentum"
        alg_match = re.search(r"algorithms=([a-zA-Z0-9_,]+)", args_str, re.IGNORECASE)
        if alg_match:
            algorithms = alg_match.group(1).lower()

        # Consume blocks if multiline directive
        blocks.pop(0)
        while blocks:
            blk = blocks[0].strip()
            if self.END_RE.match(blk):
                blocks.pop(0)
                break
            break

        CanvasWalkerBlockProcessor._counter += 1
        widget_id = f"lantern-walker-{CanvasWalkerBlockProcessor._counter}"

        if self.compiler is not None:
            self.compiler.has_walker = True

        walker_html = f"""
<div class="lantern-walker-container" id="{widget_id}" data-landscape="{html.escape(landscape)}" data-algorithms="{html.escape(algorithms)}">
  <div class="lantern-walker-header">
    <div class="lantern-walker-title">
      <span class="lantern-badge" style="margin-bottom: 0;">Interactive Simulation</span>
      <h3>Optimization Trajectory Walker</h3>
    </div>
    <div class="lantern-walker-actions">
      <button class="lantern-btn lantern-btn-sm" data-action="reset">Reset ↺</button>
      <button class="lantern-btn lantern-btn-sm lantern-btn-primary" data-action="play">Step →</button>
      <button class="lantern-btn lantern-btn-sm lantern-btn-secondary" data-action="animate">Animate ▶</button>
    </div>
  </div>

  <div class="lantern-walker-layout">
    <!-- Left: Canvas -->
    <div class="lantern-walker-canvas-pane">
      <canvas class="lantern-walker-canvas"></canvas>
      <div class="lantern-canvas-hint">Click or drag anywhere on the canvas to seed starting coordinate $(x_0, y_0)$</div>
    </div>

    <!-- Right: Sidebar Controls & Metrics -->
    <div class="lantern-walker-sidebar">
      <!-- Landscape Selection -->
      <div style="display: flex; flex-direction: column; gap: 0.35rem;">
        <label style="font-size: 0.8rem; color: var(--text-secondary); font-weight: 600;">Objective Landscape</label>
        <select data-control="landscape" style="padding: 0.45rem 0.75rem; border-radius: var(--radius-sm); background: var(--bg-surface); border: 1px solid var(--border-medium); color: var(--text-primary); font-family: var(--font-sans); outline: none;">
          <option value="rosenbrock">Rosenbrock Valley ($f = (1-x)^2 + 100(y-x^2)^2$)</option>
          <option value="ellipse">Ill-Conditioned Ellipse ($f = \\frac{1}{2}(x^2 + 20y^2)$)</option>
          <option value="rastrigin">Rastrigin Multimodal ($f = 20 + x^2 - 10\\cos(2\\pi x) + \\dots$)</option>
          <option value="saddle">Hyperbolic Saddle ($f = x^2 - y^2$)</option>
        </select>
      </div>

      <!-- Algorithm Selectors -->
      <div style="display: flex; flex-direction: column; gap: 0.35rem;">
        <label style="font-size: 0.8rem; color: var(--text-secondary); font-weight: 600;">Algorithms</label>
        <div class="lantern-algo-tags"></div>
      </div>

      <!-- Sliders -->
      <div class="lantern-slider-group">
        <div class="lantern-slider-header">
          <span>Learning Rate ($\\alpha$)</span>
          <span class="lantern-slider-val" data-val="alpha">0.0020</span>
        </div>
        <input type="range" class="lantern-slider" data-control="alpha" min="0.0001" max="0.1" step="0.0005" value="0.002" />
      </div>

      <div class="lantern-slider-group">
        <div class="lantern-slider-header">
          <span>Momentum Factor ($\\beta$)</span>
          <span class="lantern-slider-val" data-val="beta">0.85</span>
        </div>
        <input type="range" class="lantern-slider" data-control="beta" min="0.0" max="0.99" step="0.05" value="0.85" />
      </div>

      <div class="lantern-slider-group">
        <div class="lantern-slider-header">
          <span>Max Iterations</span>
          <span class="lantern-slider-val" data-val="steps">60</span>
        </div>
        <input type="range" class="lantern-slider" data-control="steps" min="5" max="150" step="5" value="60" />
      </div>

      <!-- Real-time Metrics Readout -->
      <div class="lantern-metrics-box">
        <div class="lantern-metric-item">
          <span class="lantern-metric-label">Step / Total</span>
          <span class="lantern-metric-value" data-metric="iter">0 / 60</span>
        </div>
        <div class="lantern-metric-item">
          <span class="lantern-metric-label">Coordinates</span>
          <span class="lantern-metric-value" data-metric="coord">(0.000, 0.000)</span>
        </div>
        <div class="lantern-metric-item">
          <span class="lantern-metric-label">Objective Value $f(x)$</span>
          <span class="lantern-metric-value" data-metric="fval">0.0000</span>
        </div>
        <div class="lantern-metric-item">
          <span class="lantern-metric-label">Gradient Norm $\\|\\nabla f\\|$</span>
          <span class="lantern-metric-value" data-metric="grad">0.0000</span>
        </div>
      </div>
    </div>
  </div>
</div>
"""
        placeholder = self.parser.md.htmlStash.store(walker_html)
        p = etree.SubElement(parent, "div")
        p.text = placeholder
        return True
