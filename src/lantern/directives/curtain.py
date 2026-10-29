"""Curtain directive for interactive before/after draggable split comparison (::: curtain ...)."""

from __future__ import annotations

import re
from typing import Any
import xml.etree.ElementTree as etree
from markdown.blockprocessors import BlockProcessor


class CurtainBlockProcessor(BlockProcessor):
    """Processes ::: curtain blocks."""

    START_RE = re.compile(
        r"^:::\s*curtain(?:\s+(?P<args>.*))?$",
        re.IGNORECASE,
    )
    END_RE = re.compile(r"^:::\s*$")
    PANEL_SEP_RE = re.compile(r"^===\s*(?P<title>.*?)\s*$", re.IGNORECASE)

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

        CurtainBlockProcessor._counter += 1
        curtain_id = f"lantern-curtain-{CurtainBlockProcessor._counter}"
        id_match = re.search(r'id=(?:["\'])(.*?)(?:["\'])', args_str, re.IGNORECASE)
        if id_match:
            curtain_id = id_match.group(1).strip()

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

        # Parse before and after panels
        panels: list[tuple[str, list[str]]] = []
        curr_title = ""
        curr_blocks: list[str] = []

        for blk in accumulated:
            lines = blk.splitlines()
            if lines and self.PANEL_SEP_RE.match(lines[0].strip()):
                if curr_blocks or curr_title:
                    panels.append((curr_title or "Before", curr_blocks))
                    curr_blocks = []
                curr_title = self.PANEL_SEP_RE.match(lines[0].strip()).group("title").strip()
                if len(lines) > 1:
                    curr_blocks.append("\n".join(lines[1:]))
            else:
                curr_blocks.append(blk)

        if curr_blocks or curr_title:
            panels.append((curr_title or "After", curr_blocks))

        before_title, before_blocks = panels[0] if len(panels) > 0 else ("Before", [])
        after_title, after_blocks = panels[1] if len(panels) > 1 else ("After", [])

        # Render Curtain HTML
        curtain = etree.SubElement(parent, "div")
        curtain.set("class", "lantern-curtain")
        curtain.set("id", curtain_id)

        # Before Pane
        before_pane = etree.SubElement(curtain, "div")
        before_pane.set("class", "lantern-curtain-pane lantern-curtain-before")
        before_hdr = etree.SubElement(before_pane, "div")
        before_hdr.set("class", "lantern-curtain-badge")
        before_hdr.text = before_title
        before_body = etree.SubElement(before_pane, "div")
        before_body.set("class", "lantern-curtain-body")
        if before_blocks:
            self.parser.parseBlocks(before_body, before_blocks)

        # After Pane
        after_pane = etree.SubElement(curtain, "div")
        after_pane.set("class", "lantern-curtain-pane lantern-curtain-after")
        after_hdr = etree.SubElement(after_pane, "div")
        after_hdr.set("class", "lantern-curtain-badge")
        after_hdr.text = after_title
        after_body = etree.SubElement(after_pane, "div")
        after_body.set("class", "lantern-curtain-body")
        if after_blocks:
            self.parser.parseBlocks(after_body, after_blocks)

        # Splitter Handle
        handle = etree.SubElement(curtain, "div")
        handle.set("class", "lantern-curtain-slider")
        handle_thumb = etree.SubElement(handle, "div")
        handle_thumb.set("class", "lantern-curtain-thumb")
        handle_thumb.text = "⬌"

        return True
