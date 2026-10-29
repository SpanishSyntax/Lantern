"""Math plot directive for live formula evaluation and 60 FPS slider exploration (::: math-plot ...)."""

from __future__ import annotations

import html
import re
from typing import Any
import xml.etree.ElementTree as etree
from markdown.blockprocessors import BlockProcessor


class MathPlotBlockProcessor(BlockProcessor):
    """Processes ::: math-plot fn="..." [domain="min, max"] [height="360px"] [title="..."] blocks."""

    START_RE = re.compile(
        r"^:::\s*math-plot(?:\s+(?P<args>.*))?$",
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

        MathPlotBlockProcessor._counter += 1
        plot_id = f"lantern-math-plot-{MathPlotBlockProcessor._counter}"
        fn_expr = "Math.sin(x)"
        domain_str = "0, 10"
        height = "360px"
        title = ""

        def extract_arg(param: str, default: str) -> str:
            m = re.search(r'\b' + param + r'=(?:["\'])(.*?)(?:["\'])', args_str, re.IGNORECASE)
            if not m:
                m = re.search(r'\b' + param + r'=([^\s]+)', args_str, re.IGNORECASE)
            return m.group(1).strip() if m else default

        fn_expr = extract_arg("fn", fn_expr)
        domain_str = extract_arg("domain", domain_str)
        height = extract_arg("height", height)
        title = extract_arg("title", title)

        # Consume blocks if multiline directive
        blocks.pop(0)
        while blocks:
            blk = blocks[0].strip()
            if self.END_RE.match(blk):
                blocks.pop(0)
                break
            break

        # Parse domain
        domain_parts = [p.strip() for p in domain_str.replace("[", "").replace("]", "").split(",")]
        x_min = float(domain_parts[0]) if len(domain_parts) > 0 and domain_parts[0] else 0.0
        x_max = float(domain_parts[1]) if len(domain_parts) > 1 and domain_parts[1] else 10.0
        if x_min >= x_max:
            x_max = x_min + 1.0

        num_height = int(re.sub(r"[^0-9]", "", height) or "360")
        title_html = (
            f'<div class="lantern-plot-title"><span title="{html.escape(title)}">{html.escape(title)}</span></div>'
            if title
            else '<div class="lantern-plot-title"></div>'
        )

        plot_html = f"""
<div class="lantern-plot-wrapper lantern-math-plot-wrapper" id="{plot_id}">
  <div class="lantern-plot-header">
    {title_html}
    <div class="lantern-plot-actions">
      <button class="lantern-btn lantern-btn-sm lantern-lightbox-trigger" data-target="{plot_id}" title="Toggle Fullscreen Lightbox">⛶ Lightbox</button>
    </div>
  </div>
  <div class="lantern-plot-content" style="min-height: {height}; position: relative; padding: 0;">
    <canvas class="lantern-math-canvas" id="canvas-{plot_id}" style="width: 100%; height: 100%; min-height: {height}; display: block;"></canvas>
  </div>
  <script>
  (function() {{
    const canvas = document.getElementById('canvas-{plot_id}');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const xMin = {x_min};
    const xMax = {x_max};
    const rawFn = {repr(fn_expr)};

    let hoverPt = null;

    function render() {{
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      const w = Math.max(200, Math.floor(rect.width));
      const h = Math.max(150, Math.floor(rect.height || {num_height}));
      if (canvas.width !== w * dpr || canvas.height !== h * dpr) {{
        canvas.width = w * dpr;
        canvas.height = h * dpr;
      }}
      ctx.resetTransform?.();
      ctx.scale(dpr, dpr);

      // Background
      ctx.fillStyle = '#080d16';
      ctx.fillRect(0, 0, w, h);

      // Parameter lookup proxy
      const getVal = (id, def) => (window.lantern && window.lantern.get ? window.lantern.get(id, def) : def);

      // Compile function safely
      let evalFn;
      try {{
        evalFn = new Function('x', 'Math', 'get', `
          with (Math) {{
            const omega = get('omega', get('freq', 2.0));
            const gamma = get('gamma', get('damping', 0.2));
            const alpha = get('alpha', 1.0);
            const beta = get('beta', 1.0);
            const k = get('k', 1.0);
            const A = get('A', get('amplitude', 1.0));
            return (${{rawFn}});
          }}
        `);
      }} catch (e) {{
        ctx.fillStyle = '#f43f5e';
        ctx.font = '13px monospace';
        ctx.fillText('Expression Syntax Error: ' + e.message, 20, 30);
        return;
      }}

      // Sample points
      const samples = Math.max(100, Math.min(1000, Math.floor(w)));
      const pts = [];
      let yMin = Infinity;
      let yMax = -Infinity;

      for (let i = 0; i <= samples; i++) {{
        const x = xMin + (i / samples) * (xMax - xMin);
        let y = 0;
        try {{
          y = evalFn(x, Math, getVal);
        }} catch (err) {{
          y = 0;
        }}
        if (!isNaN(y) && isFinite(y)) {{
          pts.push({{ x, y }});
          if (y < yMin) yMin = y;
          if (y > yMax) yMax = y;
        }}
      }}

      if (!pts.length) return;
      if (yMin === yMax) {{
        yMin -= 1.0;
        yMax += 1.0;
      }}
      // Padding
      const ySpan = yMax - yMin;
      yMin -= ySpan * 0.12;
      yMax += ySpan * 0.12;

      const padX = 45;
      const padY = 30;
      const plotW = w - padX - 20;
      const plotH = h - padY - 25;

      const toScreenX = (x) => padX + ((x - xMin) / (xMax - xMin)) * plotW;
      const toScreenY = (y) => padY + plotH - ((y - yMin) / (yMax - yMin)) * plotH;

      // Draw Grid lines
      ctx.strokeStyle = '#1e293b';
      ctx.lineWidth = 1;
      ctx.setLineDash([3, 3]);

      const xTicks = 5;
      for (let i = 0; i <= xTicks; i++) {{
        const tx = xMin + (i / xTicks) * (xMax - xMin);
        const sx = toScreenX(tx);
        ctx.beginPath();
        ctx.moveTo(sx, padY);
        ctx.lineTo(sx, padY + plotH);
        ctx.stroke();

        ctx.fillStyle = '#64748b';
        ctx.font = '10px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(tx.toFixed(1), sx, padY + plotH + 15);
      }}

      const yTicks = 4;
      for (let i = 0; i <= yTicks; i++) {{
        const ty = yMin + (i / yTicks) * (yMax - yMin);
        const sy = toScreenY(ty);
        ctx.beginPath();
        ctx.moveTo(padX, sy);
        ctx.lineTo(padX + plotW, sy);
        ctx.stroke();

        ctx.fillStyle = '#64748b';
        ctx.font = '10px monospace';
        ctx.textAlign = 'right';
        ctx.fillText(ty.toFixed(1), padX - 8, sy + 3);
      }}
      ctx.setLineDash([]);

      // Zero axes if inside bounds
      if (yMin <= 0 && yMax >= 0) {{
        const zeroY = toScreenY(0);
        ctx.strokeStyle = '#334155';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(padX, zeroY);
        ctx.lineTo(padX + plotW, zeroY);
        ctx.stroke();
      }}

      // Draw Curve
      ctx.strokeStyle = '#06b6d4';
      ctx.lineWidth = 2.5;
      ctx.shadowColor = 'rgba(6, 182, 212, 0.45)';
      ctx.shadowBlur = 8;
      ctx.beginPath();
      pts.forEach((pt, idx) => {{
        const sx = toScreenX(pt.x);
        const sy = toScreenY(pt.y);
        if (idx === 0) ctx.moveTo(sx, sy);
        else ctx.lineTo(sx, sy);
      }});
      ctx.stroke();
      ctx.shadowBlur = 0;

      // Hover Crosshair
      if (hoverPt && hoverPt.x >= padX && hoverPt.x <= padX + plotW) {{
        const hoverX = xMin + ((hoverPt.x - padX) / plotW) * (xMax - xMin);
        let hoverY = 0;
        try {{ hoverY = evalFn(hoverX, Math, getVal); }} catch(e) {{}}
        const sy = toScreenY(hoverY);

        ctx.strokeStyle = '#a855f7';
        ctx.lineWidth = 1;
        ctx.setLineDash([2, 2]);
        ctx.beginPath();
        ctx.moveTo(hoverPt.x, padY);
        ctx.lineTo(hoverPt.x, padY + plotH);
        ctx.moveTo(padX, sy);
        ctx.lineTo(padX + plotW, sy);
        ctx.stroke();
        ctx.setLineDash([]);

        ctx.fillStyle = '#a855f7';
        ctx.beginPath();
        ctx.arc(hoverPt.x, sy, 4, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = '#f8fafc';
        ctx.font = '11px monospace';
        ctx.textAlign = 'left';
        ctx.fillText(`x: ${{hoverX.toFixed(2)}}  y: ${{hoverY.toFixed(3)}}`, padX + 10, padY + 15);
      }}
    }}

    render();
    window.addEventListener('resize', render);
    window.addEventListener('lantern:input', render);

    canvas.addEventListener('mousemove', (e) => {{
      const rect = canvas.getBoundingClientRect();
      hoverPt = {{ x: e.clientX - rect.left, y: e.clientY - rect.top }};
      render();
    }});

    canvas.addEventListener('mouseleave', () => {{
      hoverPt = null;
      render();
    }});
  }})();
  </script>
</div>
"""

        placeholder = self.parser.md.htmlStash.store(plot_html)
        if len(parent):
            parent[-1].tail = (parent[-1].tail or "") + f"\n{placeholder}\n"
        else:
            parent.text = (parent.text or "") + f"\n{placeholder}\n"
        return True
