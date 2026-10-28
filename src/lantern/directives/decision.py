"""Decision Ladder directive processor for Lantern (::: decision-ladder ...)."""

from __future__ import annotations

import html
import json
import os
from pathlib import Path
import re
from typing import Any
import xml.etree.ElementTree as etree
from markdown.blockprocessors import BlockProcessor


class DecisionLadderBlockProcessor(BlockProcessor):
    """Processes ::: decision-ladder [questions=path.json] blocks."""

    START_RE = re.compile(
        r"^:::\s*decision-ladder(?:\s+(?P<args>.*))?$",
        re.IGNORECASE,
    )
    END_RE = re.compile(r"^:::\s*$")

    _counter = 0

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

        args_str = match.group("args") or ""

        # Check for questions=path.json
        json_content = None
        q_match = re.search(r"questions=([^\s]+)", args_str)
        if q_match:
            q_file = q_match.group(1).strip("\"'")
            q_path = (self.base_dir / q_file).resolve()
            if q_path.exists():
                try:
                    json_content = q_path.read_text(encoding="utf-8")
                except Exception:
                    pass

        # Check if block has embedded JSON
        inside_lines = blocks[0].strip().splitlines()[1:]
        blocks.pop(0)

        accumulated_lines = list(inside_lines)
        while blocks:
            blk = blocks.pop(0)
            lines = blk.splitlines()
            if lines and self.END_RE.match(lines[-1].strip()):
                if len(lines) > 1:
                    accumulated_lines.extend(lines[:-1])
                break
            elif self.END_RE.match(blk.strip()):
                break
            else:
                accumulated_lines.append(blk)

        if not json_content and accumulated_lines:
            raw_text = "\n".join(accumulated_lines).strip()
            if raw_text.startswith("{") and raw_text.endswith("}"):
                try:
                    # Validate JSON
                    json.loads(raw_text)
                    json_content = raw_text
                except Exception:
                    pass

        DecisionLadderBlockProcessor._counter += 1
        widget_id = f"lantern-decision-{DecisionLadderBlockProcessor._counter}"

        if self.compiler is not None:
            self.compiler.has_decision = True

        script_tag = f'<script type="application/json">{json_content}</script>' if json_content else ""

        ladder_html = f"""
<div class="lantern-decision-container" id="{widget_id}">
  <div class="lantern-decision-header">
    <span class="lantern-badge">Interactive Flowchart</span>
    <h3 style="font-size: 1.35rem; font-weight: 700; color: var(--text-primary); margin-top: 0.25rem;">
      Algorithm & Strategy Decision Ladder
    </h3>
    <p style="font-size: 0.9rem; color: var(--text-secondary); margin-top: 0.25rem;">
      Follow the branching questions below to pinpoint the optimal solver and mathematical convergence guarantees for your problem.
    </p>
  </div>

  <div class="lantern-decision-card">
    <!-- Rendered dynamically by decision.js -->
  </div>
  {script_tag}
</div>
"""
        placeholder = self.parser.md.htmlStash.store(ladder_html)
        p = etree.SubElement(parent, "div")
        p.text = placeholder
        return True
