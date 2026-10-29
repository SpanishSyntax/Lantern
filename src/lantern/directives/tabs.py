"""Tabs directive for multi-perspective tabbed content switcher (::: tabs ...)."""

from __future__ import annotations

import re
from typing import Any
import xml.etree.ElementTree as etree
from markdown.blockprocessors import BlockProcessor

from lantern.directives.utils import extract_directive_blocks


class TabsBlockProcessor(BlockProcessor):
    """Processes ::: tabs [id="..."] blocks with === Tab Title dividers."""

    START_RE = re.compile(
        r"^:::\s*tabs(?:\s+(?P<args>.*))?$",
        re.IGNORECASE,
    )
    TAB_SEP_RE = re.compile(r"^===\s*(?P<title>.*?)\s*$", re.IGNORECASE)

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

        TabsBlockProcessor._counter += 1
        tabs_id = f"tabs-{TabsBlockProcessor._counter}"
        id_match = re.search(r'id=(?:["\'])(.*?)(?:["\'])', args_str, re.IGNORECASE)
        if id_match:
            tabs_id = id_match.group(1).strip()

        # Extract blocks inside the directive with depth tracking
        accumulated = extract_directive_blocks(blocks)

        # Parse tabs
        tab_list: list[tuple[str, list[str]]] = []
        curr_title = ""
        curr_blocks: list[str] = []

        for blk in accumulated:
            lines = blk.splitlines()
            if lines and self.TAB_SEP_RE.match(lines[0].strip()):
                if curr_blocks or curr_title:
                    tab_list.append((curr_title or f"Tab {len(tab_list) + 1}", curr_blocks))
                    curr_blocks = []
                curr_title = self.TAB_SEP_RE.match(lines[0].strip()).group("title").strip()
                if len(lines) > 1:
                    curr_blocks.append("\n".join(lines[1:]))
            else:
                curr_blocks.append(blk)

        if curr_blocks or curr_title:
            tab_list.append((curr_title or f"Tab {len(tab_list) + 1}", curr_blocks))

        if not tab_list:
            tab_list = [("Tab 1", accumulated)]

        # Render Tabs HTML
        tabs_container = etree.SubElement(parent, "div")
        tabs_container.set("class", "lantern-tabs")
        tabs_container.set("id", tabs_id)

        # Tab Bar
        tab_bar = etree.SubElement(tabs_container, "div")
        tab_bar.set("class", "lantern-tabs-bar")

        for idx, (title, _) in enumerate(tab_list):
            btn = etree.SubElement(tab_bar, "button")
            btn.set("type", "button")
            btn.set("class", f"lantern-tab-btn{' active' if idx == 0 else ''}")
            btn.set("data-tab-target", str(idx))
            btn.text = title

        # Panes
        panes = etree.SubElement(tabs_container, "div")
        panes.set("class", "lantern-tabs-panes")

        for idx, (_, tab_blocks) in enumerate(tab_list):
            pane = etree.SubElement(panes, "div")
            pane.set("class", f"lantern-tab-pane{' active' if idx == 0 else ''}")
            pane.set("data-tab-index", str(idx))
            if tab_blocks:
                self.parser.parseBlocks(pane, tab_blocks)

        return True
