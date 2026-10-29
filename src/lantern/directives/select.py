"""Select directive for dropdown choices (::: select ...)."""

from __future__ import annotations

import re
from typing import Any
import xml.etree.ElementTree as etree
from markdown.blockprocessors import BlockProcessor


class SelectBlockProcessor(BlockProcessor):
    """Processes ::: select id="..." label="..." default="..." blocks with list items - [key]: Label."""

    START_RE = re.compile(
        r"^:::\s*select(?:\s+(?P<args>.*))?$",
        re.IGNORECASE,
    )
    END_RE = re.compile(r"^:::\s*$")
    ITEM_RE = re.compile(r"^[-*]\s*\[(?P<val>[^\]]+)\]:\s*(?P<label>.*)$")

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

        SelectBlockProcessor._counter += 1
        sel_id = f"select-{SelectBlockProcessor._counter}"
        label = "Select Option"
        default_val = ""

        def extract_arg(param: str, default: str) -> str:
            m = re.search(r'\b' + param + r'=(?:["\'])(.*?)(?:["\'])', args_str, re.IGNORECASE)
            if not m:
                m = re.search(r'\b' + param + r'=([^\s]+)', args_str, re.IGNORECASE)
            return m.group(1).strip() if m else default

        sel_id = extract_arg("id", sel_id)
        label = extract_arg("label", label)
        default_val = extract_arg("default", default_val)

        # Extract blocks inside the directive
        first_block_rest = "\n".join(blocks[0].strip().splitlines()[1:])
        blocks.pop(0)

        accumulated: list[str] = []
        if first_block_rest.strip():
            accumulated.append(first_block_rest)

        while blocks:
            blk = blocks.pop(0)
            lines = blk.splitlines()
            if lines and self.END_RE.match(lines[-1].strip()):
                if len(lines) > 1:
                    accumulated.append("\n".join(lines[:-1]))
                break
            elif self.END_RE.match(blk.strip()):
                break
            else:
                accumulated.append(blk)

        # Parse options
        options: list[tuple[str, str]] = []
        full_text = "\n".join(accumulated)
        for line in full_text.splitlines():
            line = line.strip()
            item_match = self.ITEM_RE.match(line)
            if item_match:
                options.append((item_match.group("val").strip(), item_match.group("label").strip()))

        if not options:
            options = [("opt1", "Option 1"), ("opt2", "Option 2")]

        if not default_val and options:
            default_val = options[0][0]

        # Render Select HTML
        wrap = etree.SubElement(parent, "div")
        wrap.set("class", "lantern-control-wrap lantern-control-select")
        wrap.set("data-control-id", sel_id)

        lbl = etree.SubElement(wrap, "label")
        lbl.set("class", "lantern-control-label")
        lbl.set("for", f"ctrl-{sel_id}")
        lbl.text = label

        sel = etree.SubElement(wrap, "select")
        sel.set("class", "lantern-select")
        sel.set("id", f"ctrl-{sel_id}")
        sel.set("name", sel_id)

        for val, item_label in options:
            opt = etree.SubElement(sel, "option")
            opt.set("value", val)
            if val == default_val:
                opt.set("selected", "selected")
            opt.text = item_label

        return True
