"""Switch directive for boolean state toggling (::: switch ...)."""

from __future__ import annotations

import re
from typing import Any
import xml.etree.ElementTree as etree
from markdown.blockprocessors import BlockProcessor


class SwitchBlockProcessor(BlockProcessor):
    """Processes ::: switch id="..." label="..." [default=true|false] blocks."""

    START_RE = re.compile(
        r"^:::\s*switch(?:\s+(?P<args>.*))?$",
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

        SwitchBlockProcessor._counter += 1
        switch_id = f"switch-{SwitchBlockProcessor._counter}"
        label = "Toggle Option"
        default_val = "false"

        def extract_arg(param: str, default: str) -> str:
            m = re.search(r'\b' + param + r'=(?:["\'])(.*?)(?:["\'])', args_str, re.IGNORECASE)
            if not m:
                m = re.search(r'\b' + param + r'=([^\s]+)', args_str, re.IGNORECASE)
            return m.group(1).strip() if m else default

        switch_id = extract_arg("id", switch_id)
        label = extract_arg("label", label)
        default_val = extract_arg("default", default_val).lower()
        is_checked = default_val in ("true", "1", "yes")

        # Consume blocks if multiline directive
        blocks.pop(0)
        while blocks:
            blk = blocks[0].strip()
            if self.END_RE.match(blk):
                blocks.pop(0)
                break
            break

        # Render Switch HTML
        wrap = etree.SubElement(parent, "div")
        wrap.set("class", "lantern-control-wrap lantern-control-switch")
        wrap.set("data-control-id", switch_id)

        lbl = etree.SubElement(wrap, "label")
        lbl.set("class", "lantern-switch-label")
        lbl.set("for", f"ctrl-{switch_id}")

        text_span = etree.SubElement(lbl, "span")
        text_span.set("class", "lantern-control-label")
        text_span.text = label

        switch_box = etree.SubElement(lbl, "div")
        switch_box.set("class", "lantern-switch")

        cb = etree.SubElement(switch_box, "input")
        cb.set("type", "checkbox")
        cb.set("id", f"ctrl-{switch_id}")
        cb.set("name", switch_id)
        if is_checked:
            cb.set("checked", "checked")

        slider_span = etree.SubElement(switch_box, "span")
        slider_span.set("class", "lantern-switch-slider")

        return True
