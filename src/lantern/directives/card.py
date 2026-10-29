"""Card directive for glassmorphic bordered container boxes (::: card ...)."""

from __future__ import annotations

import re
from typing import Any
import xml.etree.ElementTree as etree
from markdown.blockprocessors import BlockProcessor

from lantern.directives.utils import extract_directive_blocks


class CardBlockProcessor(BlockProcessor):
    """Processes ::: card [title="..."] [badge="..."] [icon="..."] blocks."""

    START_RE = re.compile(
        r"^:::\s*card(?:\s+(?P<args>.*))?$",
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

        # Parse title, badge, icon
        title = ""
        badge = ""
        icon = ""

        t_match = re.search(r'title=(?:["\'])(.*?)(?:["\'])', args_str, re.IGNORECASE)
        if t_match:
            title = t_match.group(1).strip()

        b_match = re.search(r'badge=(?:["\'])(.*?)(?:["\'])', args_str, re.IGNORECASE)
        if b_match:
            badge = b_match.group(1).strip()

        i_match = re.search(r'icon=(?:["\'])(.*?)(?:["\'])', args_str, re.IGNORECASE)
        if i_match:
            icon = i_match.group(1).strip()

        # Extract blocks inside the directive with depth tracking
        accumulated = extract_directive_blocks(blocks)

        # Build Card HTML
        card = etree.SubElement(parent, "div")
        card.set("class", "lantern-card")

        if title or badge or icon:
            header = etree.SubElement(card, "div")
            header.set("class", "lantern-card-header")

            title_wrap = etree.SubElement(header, "div")
            title_wrap.set("class", "lantern-card-title-wrap")

            if icon:
                icon_span = etree.SubElement(title_wrap, "span")
                icon_span.set("class", "lantern-card-icon")
                icon_span.text = icon

            if title:
                t_el = etree.SubElement(title_wrap, "h4")
                t_el.set("class", "lantern-card-title")
                t_el.text = title

            if badge:
                badge_el = etree.SubElement(header, "span")
                badge_el.set("class", "lantern-badge")
                badge_el.set("style", "margin-bottom: 0;")
                badge_el.text = badge

        body = etree.SubElement(card, "div")
        body.set("class", "lantern-card-body")

        if accumulated:
            self.parser.parseBlocks(body, accumulated)

        return True
