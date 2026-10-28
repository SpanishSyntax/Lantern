"""Barrier vs. Penalty directive processor for Lantern (::: barrier-vs-penalty)."""

from __future__ import annotations

import re
from typing import Any
import xml.etree.ElementTree as etree
from markdown.blockprocessors import BlockProcessor


class BarrierBlockProcessor(BlockProcessor):
    """Processes ::: barrier-vs-penalty blocks."""

    START_RE = re.compile(
        r"^:::\s*barrier-vs-penalty(?:\s+.*)?$",
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
        if not self.START_RE.match(lines[0]):
            return False

        # Consume blocks if multiline directive
        blocks.pop(0)
        while blocks:
            blk = blocks[0].strip()
            if self.END_RE.match(blk):
                blocks.pop(0)
                break
            break

        BarrierBlockProcessor._counter += 1
        widget_id = f"lantern-barrier-{BarrierBlockProcessor._counter}"

        if self.compiler is not None:
            self.compiler.has_barrier = True

        barrier_html = f"""
<div class="lantern-barrier-container" id="{widget_id}">
  <div class="lantern-barrier-header">
    <div class="lantern-barrier-title">
      <span class="lantern-badge" style="background: rgba(251, 191, 36, 0.15); color: #fbbf24; border-color: rgba(251, 191, 36, 0.3); margin-bottom: 0;">Constraint Boundary Lab</span>
      <h3 style="font-size: 1.25rem; font-weight: 700; color: var(--text-primary); margin-top: 0.25rem;">Barrier vs. Penalty Method Dynamics</h3>
    </div>
    <!-- Mode Radios -->
    <div style="display: flex; gap: 1rem; align-items: center; background: var(--bg-deep); padding: 0.4rem 0.8rem; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle); font-size: 0.85rem;">
      <label style="display: flex; align-items: center; gap: 0.35rem; cursor: pointer; color: var(--text-primary);">
        <input type="radio" name="barrier_mode_{widget_id}" data-control="mode" value="penalty" checked />
        <span>Quadratic Penalty ($P_\\mu$)</span>
      </label>
      <label style="display: flex; align-items: center; gap: 0.35rem; cursor: pointer; color: var(--text-primary);">
        <input type="radio" name="barrier_mode_{widget_id}" data-control="mode" value="barrier" />
        <span>Logarithmic Barrier ($B_\\mu$)</span>
      </label>
    </div>
  </div>

  <div class="lantern-barrier-controls">
    <div class="lantern-slider-group" style="flex: 1; min-width: 260px;">
      <div class="lantern-slider-header">
        <span data-label="mu">Penalty Multiplier $\\mu$ ($\\to \\infty$)</span>
        <span class="lantern-slider-val" data-val="mu">1.00</span>
      </div>
      <input type="range" class="lantern-slider" data-control="mu" min="-1" max="1.6" step="0.05" value="0" />
    </div>

    <!-- Readout Summary -->
    <div style="display: flex; gap: 1.5rem; flex-wrap: wrap; font-size: 0.85rem;">
      <div>
        <span style="color: var(--text-muted); display: block; font-size: 0.75rem;">Current Minimum $x^*(\\\\mu)$</span>
        <strong style="color: var(--cyan); font-family: var(--font-mono);" data-metric="pos">(1.300, 1.300)</strong>
      </div>
      <div>
        <span style="color: var(--text-muted); display: block; font-size: 0.75rem;">Objective $f(x)$</span>
        <strong style="color: var(--text-primary); font-family: var(--font-mono);" data-metric="f">1.4400</strong>
      </div>
      <div>
        <span style="color: var(--text-muted); display: block; font-size: 0.75rem;">Violation $\\max(0, g)$</span>
        <strong style="color: #fbbf24; font-family: var(--font-mono);" data-metric="viol">0.600</strong>
      </div>
      <div>
        <span style="color: var(--text-muted); display: block; font-size: 0.75rem;">Status</span>
        <strong style="color: #34d399;" data-metric="status">Infeasible</strong>
      </div>
    </div>
  </div>

  <!-- Dual Plot Views -->
  <div class="lantern-barrier-views">
    <div class="lantern-barrier-plot-pane">
      <canvas class="lantern-barrier-canvas lantern-barrier-canvas-2d"></canvas>
    </div>
    <div class="lantern-barrier-plot-pane">
      <canvas class="lantern-barrier-canvas lantern-barrier-canvas-1d"></canvas>
    </div>
  </div>
</div>
"""
        placeholder = self.parser.md.htmlStash.store(barrier_html)
        p = etree.SubElement(parent, "div")
        p.text = placeholder
        return True
