"""Metrics directive for KPI and stat readout decks (::: metrics ...)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as etree

from markdown.blockprocessors import BlockProcessor

from lantern.directives.utils import extract_directive_blocks


class MetricsBlockProcessor(BlockProcessor):
    """Processes ::: metrics [cols=4] blocks with list items - Label: Value [badge=color]."""

    START_RE = re.compile(
        r"^:::\s*metrics(?:\s+(?P<args>.*))?$",
        re.IGNORECASE,
    )
    END_RE = re.compile(r"^:::\s*$")
    ITEM_RE = re.compile(
        r"^[-*]\s*(?P<label>[^:]+):\s*(?P<val>[^\[\n]+)(?:\s*\[badge=(?P<badge>[^\]]+)\])?\s*$",
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

        # Parse cols
        cols = 4
        c_match = re.search(r"cols=(\d+)", args_str, re.IGNORECASE)
        if c_match:
            cols = max(1, min(6, int(c_match.group(1))))

        # Extract blocks inside the directive
        accumulated = extract_directive_blocks(blocks)

        # Parse items
        items: list[tuple[str, str, str]] = []
        full_text = "\n".join(accumulated)
        for line in full_text.splitlines():
            line = line.strip()
            m = self.ITEM_RE.match(line)
            if m:
                label = m.group("label").strip()
                val = m.group("val").strip()
                badge = (m.group("badge") or "").strip()
                items.append((label, val, badge))

        # Render Metrics Deck HTML
        deck = etree.SubElement(parent, "div")
        deck.set("class", "lantern-metrics-deck")
        deck.set(
            "style",
            f"display: grid; grid-template-columns: repeat({cols}, minmax(180px, 1fr)); gap: 1rem;",
        )

        for label, val, badge in items:
            card = etree.SubElement(deck, "div")
            card.set("class", "lantern-metric-card")

            lbl_el = etree.SubElement(card, "div")
            lbl_el.set("class", "lantern-metric-label")
            lbl_el.text = label

            val_wrap = etree.SubElement(card, "div")
            val_wrap.set("class", "lantern-metric-val-wrap")

            val_el = etree.SubElement(val_wrap, "span")
            val_el.set("class", "lantern-metric-value")
            val_el.text = val

            if badge:
                badge_el = etree.SubElement(val_wrap, "span")
                badge_el.set("class", f"lantern-badge lantern-badge-{badge}")
                badge_el.set(
                    "style",
                    "margin-bottom: 0; font-size: 0.7rem; padding: 0.15rem 0.5rem;",
                )
                badge_el.text = badge.title()

        return True
