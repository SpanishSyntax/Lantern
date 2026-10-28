"""Callout alert block processor for Lantern (::: callout type=...)."""

from __future__ import annotations

import re
from typing import Any
import xml.etree.ElementTree as etree
from markdown.blockprocessors import BlockProcessor


class CalloutBlockProcessor(BlockProcessor):
    """Processes ::: callout type=[note|tip|warning|danger] blocks."""

    START_RE = re.compile(
        r"^:::\s*callout(?:\s+type=(?P<type>note|tip|warning|danger|caution))?(?:\s+title=(?P<quote>[\"'])(?P<title>.*?)(?P=quote))?\s*$",
        re.IGNORECASE,
    )
    END_RE = re.compile(r"^:::\s*$")

    ICONS = {
        "note": "ℹ",
        "tip": "💡",
        "warning": "⚠️",
        "danger": "🚨",
        "caution": "🚨",
    }

    TITLES = {
        "note": "Note",
        "tip": "Tip",
        "warning": "Warning",
        "danger": "Danger",
        "caution": "Caution",
    }

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

        callout_type = (match.group("type") or "note").lower()
        if callout_type == "caution":
            callout_type = "danger"
        title_text = match.group("title") or self.TITLES.get(callout_type, "Note")
        icon = self.ICONS.get(callout_type, "ℹ")

        # Extract blocks inside the directive
        inside_blocks: list[str] = []
        first_block_rest = "\n".join(blocks[0].strip().splitlines()[1:])
        if first_block_rest.strip():
            inside_blocks.append(first_block_rest)

        blocks.pop(0)
        closed = False

        while blocks:
            blk = blocks.pop(0)
            lines = blk.splitlines()
            if lines and self.END_RE.match(lines[-1].strip()):
                if len(lines) > 1:
                    inside_blocks.append("\n".join(lines[:-1]))
                closed = True
                break
            elif self.END_RE.match(blk.strip()):
                closed = True
                break
            else:
                inside_blocks.append(blk)

        # Build Callout HTML
        container = etree.SubElement(parent, "div")
        container.set("class", f"lantern-callout lantern-callout-{callout_type}")

        header = etree.SubElement(container, "div")
        header.set("class", "lantern-callout-header")

        icon_span = etree.SubElement(header, "span")
        icon_span.set("class", "lantern-callout-icon")
        icon_span.text = icon

        title_span = etree.SubElement(header, "span")
        title_span.set("class", "lantern-callout-title")
        title_span.text = title_text

        body = etree.SubElement(container, "div")
        body.set("class", "lantern-callout-body")

        # Parse nested markdown inside body
        if inside_blocks:
            self.parser.parseBlocks(body, inside_blocks)

        return True
