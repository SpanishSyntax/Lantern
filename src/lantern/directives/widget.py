"""Widget directive for custom generative simulations and interactive canvas labs (::: widget ...)."""

from __future__ import annotations

import html
import re
from typing import Any
import xml.etree.ElementTree as etree
from markdown.blockprocessors import BlockProcessor


from lantern.directives.utils import extract_directive_blocks


class WidgetBlockProcessor(BlockProcessor):
    """Processes ::: widget [id="..."] [height="360px"] [title="..."] blocks."""

    START_RE = re.compile(
        r"^:::\s*widget(?:\s+(?P<args>.*))?$",
        re.IGNORECASE,
    )
    END_RE = re.compile(r"^:::\s*$")

    _counter = 0

    def test(self, parent: etree.Element, block: str) -> bool:
        lines = block.strip().splitlines()
        if not lines:
            return False
        return bool(self.START_RE.match(lines[0]))

    def run(self, parent: etree.Element, blocks: list[str]) -> bool:
        if not blocks:
            return False
        first_line = blocks[0].strip().splitlines()[0]
        match = self.START_RE.match(first_line)
        if not match:
            return False

        args_str = match.group("args") or ""

        WidgetBlockProcessor._counter += 1
        widget_id = f"lantern-widget-{WidgetBlockProcessor._counter}"
        height = "360px"
        title = ""

        def extract_arg(param: str, default: str) -> str:
            m = re.search(r'\b' + param + r'=(?:["\'])(.*?)(?:["\'])', args_str, re.IGNORECASE)
            if not m:
                m = re.search(r'\b' + param + r'=([^\s]+)', args_str, re.IGNORECASE)
            return m.group(1).strip() if m else default

        widget_id = extract_arg("id", widget_id)
        height = extract_arg("height", height)
        title = extract_arg("title", title)

        # Collect inner script content using standard depth-aware block extraction
        accumulated = extract_directive_blocks(blocks)
        user_script = "\n\n".join(accumulated).strip()
        num_height = int(re.sub(r"[^0-9]", "", height) or "360")

        title_html = (
            f'<div class="lantern-plot-title"><span title="{html.escape(title)}">{html.escape(title)}</span></div>'
            if title
            else '<div class="lantern-plot-title"></div>'
        )

        widget_html = f"""
<div class="lantern-plot-wrapper lantern-widget-wrapper" id="{widget_id}">
  <div class="lantern-plot-header">
    {title_html}
    <div class="lantern-plot-actions">
      <button class="lantern-btn lantern-btn-sm lantern-lightbox-trigger" data-target="{widget_id}" title="Toggle Fullscreen Lightbox">⛶ Lightbox</button>
    </div>
  </div>
  <div class="lantern-plot-content lantern-widget-content" style="min-height: {height}; position: relative; padding: 0;">
    <canvas class="lantern-widget-canvas" id="canvas-{widget_id}" style="width: 100%; height: {height}; display: block;"></canvas>
  </div>
  <script>
  (function() {{
    const canvas = document.getElementById('canvas-{widget_id}');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    function resize() {{
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      const w = Math.max(200, Math.floor(rect.width));
      const h = Math.max(150, Math.floor(rect.height || {num_height}));
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      ctx.resetTransform?.();
      ctx.scale(dpr, dpr);
      canvas._logicalWidth = w;
      canvas._logicalHeight = h;
    }}
    resize();
    window.addEventListener('resize', resize);

    const theme = (window.lantern && window.lantern.theme) || {{
      cyan: '#06b6d4',
      purple: '#a855f7',
      emerald: '#10b981',
      amber: '#f59e0b',
      rose: '#f43f5e',
      bgCard: '#0f172a',
      bgSurface: '#1e293b',
      border: '#334155',
      textPrimary: '#f8fafc',
      textSecondary: '#94a3b8'
    }};

    try {{
      {user_script}
    }} catch (err) {{
      console.error('[Lantern Widget {widget_id} Error]', err);
    }}
  }})();
  </script>
</div>
"""

        placeholder = self.parser.md.htmlStash.store(widget_html)
        p = etree.SubElement(parent, "div")
        p.text = placeholder
        return True
