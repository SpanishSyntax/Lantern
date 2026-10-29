"""Comparison directive for 2-column before/after or A/B comparison cards (::: comparison ...)."""

from __future__ import annotations

import re
from typing import Any
import xml.etree.ElementTree as etree
from markdown.blockprocessors import BlockProcessor

from lantern.directives.utils import extract_directive_blocks


class ComparisonBlockProcessor(BlockProcessor):
    """Processes ::: comparison blocks with === Left: Title and === Right: Title."""

    START_RE = re.compile(
        r"^:::\s*comparison(?:\s+(?P<args>.*))?$",
        re.IGNORECASE,
    )
    CARD_SEP_RE = re.compile(r"^===\s*(?P<side>Left|Right)?[:\s]*(?P<title>.*?)\s*$", re.IGNORECASE)

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

        # Extract blocks inside the directive with depth tracking
        accumulated = extract_directive_blocks(blocks)

        # Parse comparison sides
        sides: list[tuple[str, str, list[str]]] = []
        curr_side = "left"
        curr_title = ""
        curr_blocks: list[str] = []

        for blk in accumulated:
            lines = blk.splitlines()
            if lines and self.CARD_SEP_RE.match(lines[0].strip()):
                if curr_blocks or curr_title:
                    sides.append((curr_side, curr_title, curr_blocks))
                    curr_blocks = []
                m = self.CARD_SEP_RE.match(lines[0].strip())
                curr_side = (m.group("side") or ("right" if sides else "left")).lower()
                curr_title = (m.group("title") or "").strip()
                if len(lines) > 1:
                    curr_blocks.append("\n".join(lines[1:]))
            else:
                curr_blocks.append(blk)

        if curr_blocks or curr_title:
            sides.append((curr_side, curr_title, curr_blocks))

        if not sides:
            sides = [("left", "Method A", accumulated)]

        # Render Comparison HTML
        comp = etree.SubElement(parent, "div")
        comp.set("class", "lantern-comparison")

        for side_name, title, card_blocks in sides:
            card = etree.SubElement(comp, "div")
            card.set("class", f"lantern-comparison-card lantern-comparison-{side_name}")

            if title:
                hdr = etree.SubElement(card, "div")
                hdr.set("class", "lantern-comparison-header")

                badge = etree.SubElement(hdr, "span")
                badge.set("class", f"lantern-badge {'lantern-badge-cyan' if side_name == 'left' else 'lantern-badge-purple'}")
                badge.set("style", "margin-bottom: 0;")
                badge.text = side_name.title()

                h4 = etree.SubElement(hdr, "h4")
                h4.set("class", "lantern-comparison-title")
                h4.text = title

            body = etree.SubElement(card, "div")
            body.set("class", "lantern-comparison-body")
            if card_blocks:
                self.parser.parseBlocks(body, card_blocks)

        return True
