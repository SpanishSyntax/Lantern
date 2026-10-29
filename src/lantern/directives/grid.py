"""Grid directive for multi-column horizontal strips (::: grid ...)."""

from __future__ import annotations

import re
from typing import Any
import xml.etree.ElementTree as etree
from markdown.blockprocessors import BlockProcessor

from lantern.directives.utils import extract_directive_blocks


class GridBlockProcessor(BlockProcessor):
    """Processes ::: grid [preset | cols="..."] [gap="..."] blocks."""

    START_RE = re.compile(
        r"^:::\s*grid(?:\s+(?P<args>.*))?$",
        re.IGNORECASE,
    )
    COL_SEP_RE = re.compile(r"^(?:===\s*(?:\[(?P<bracket_title>.*?)\]|(?P<raw_title>.*?))?|---)\s*$")

    PRESETS = {
        "50/50": "1fr 1fr",
        "2-col": "1fr 1fr",
        "60/40": "1.5fr 1fr",
        "40/60": "1fr 1.5fr",
        "3-col": "repeat(3, 1fr)",
        "33/33/33": "repeat(3, 1fr)",
        "4-col": "repeat(4, 1fr)",
    }

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

        # Parse preset or custom columns
        grid_cols = "1fr 1fr"
        gap = "1.5rem"

        # Check presets
        for preset_name, css_val in self.PRESETS.items():
            if re.search(r"(?:\b|^)" + re.escape(preset_name) + r"(?:\b|$)", args_str, re.IGNORECASE):
                grid_cols = css_val
                break

        # Check cols="..."
        cols_match = re.search(r'cols=(?:["\'])(.*?)(?:["\'])', args_str, re.IGNORECASE)
        if cols_match:
            grid_cols = cols_match.group(1).strip()

        # Check gap="..."
        gap_match = re.search(r'gap=(?:["\'])(.*?)(?:["\'])', args_str, re.IGNORECASE)
        if gap_match:
            gap = gap_match.group(1).strip()

        # Extract blocks inside the directive with depth tracking
        accumulated = extract_directive_blocks(blocks)

        # Split accumulated blocks into columns using COL_SEP_RE
        columns: list[tuple[str, list[str]]] = []
        current_title = ""
        current_col_blocks: list[str] = []

        for blk in accumulated:
            lines = blk.splitlines()
            if lines and self.COL_SEP_RE.match(lines[0].strip()):
                if current_col_blocks or current_title:
                    columns.append((current_title, current_col_blocks))
                    current_col_blocks = []

                sep_match = self.COL_SEP_RE.match(lines[0].strip())
                current_title = (
                    sep_match.group("bracket_title") or sep_match.group("raw_title") or ""
                ).strip()
                if len(lines) > 1:
                    current_col_blocks.append("\n".join(lines[1:]))
            else:
                current_col_blocks.append(blk)

        if current_col_blocks or current_title:
            columns.append((current_title, current_col_blocks))

        if not columns:
            columns = [("", accumulated)]

        # Render Grid HTML
        grid_div = etree.SubElement(parent, "div")
        grid_div.set("class", "lantern-grid-strip")
        grid_div.set("style", f"display: grid; grid-template-columns: {grid_cols}; gap: {gap};")

        for title, col_blocks in columns:
            col_div = etree.SubElement(grid_div, "div")
            col_div.set("class", "lantern-grid-col")
            if title:
                hdr = etree.SubElement(col_div, "div")
                hdr.set("class", "lantern-grid-col-header")
                hdr.text = title
            if col_blocks:
                self.parser.parseBlocks(col_div, col_blocks)

        return True
