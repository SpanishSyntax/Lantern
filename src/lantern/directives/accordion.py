"""Accordion directive for collapsible deep-dives (::: accordion ...)."""

from __future__ import annotations

import re
from typing import Any
import xml.etree.ElementTree as etree
from markdown.blockprocessors import BlockProcessor

from lantern.directives.utils import extract_directive_blocks


class AccordionBlockProcessor(BlockProcessor):
    """Processes ::: accordion title="..." [open] blocks."""

    START_RE = re.compile(
        r"^:::\s*accordion(?:\s+(?P<args>.*))?$",
        re.IGNORECASE,
    )

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

        # Parse title & open
        title = "Deep Dive"
        t_match = re.search(r'title=(?:["\'])(.*?)(?:["\'])', args_str, re.IGNORECASE)
        if t_match:
            title = t_match.group(1).strip()

        is_open = bool(re.search(r"\bopen\b", args_str, re.IGNORECASE))

        # Extract blocks inside the directive with depth tracking
        accumulated = extract_directive_blocks(blocks)

        # Render Details/Summary Accordion
        details = etree.SubElement(parent, "details")
        details.set("class", "lantern-accordion")
        if is_open:
            details.set("open", "open")

        summary = etree.SubElement(details, "summary")
        summary.set("class", "lantern-accordion-summary")

        title_span = etree.SubElement(summary, "span")
        title_span.set("class", "lantern-accordion-title")
        title_span.text = title

        chevron = etree.SubElement(summary, "span")
        chevron.set("class", "lantern-accordion-chevron")
        chevron.text = "▼"

        body = etree.SubElement(details, "div")
        body.set("class", "lantern-accordion-body")

        if accumulated:
            self.parser.parseBlocks(body, accumulated)

        return True
