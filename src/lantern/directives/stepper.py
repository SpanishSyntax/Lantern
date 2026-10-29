"""Stepper directive for sequential phase walkthroughs (::: stepper ...)."""

from __future__ import annotations

import re
from typing import Any
import xml.etree.ElementTree as etree
from markdown.blockprocessors import BlockProcessor

from lantern.directives.utils import extract_directive_blocks


class StepperBlockProcessor(BlockProcessor):
    """Processes ::: stepper [id="..."] blocks."""

    START_RE = re.compile(
        r"^:::\s*stepper(?:\s+(?P<args>.*))?$",
        re.IGNORECASE,
    )
    STEP_SEP_RE = re.compile(r"^===\s*(?:Step\s*\d+[:.]?\s*)?(?P<title>.*?)\s*$", re.IGNORECASE)

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

        # Parse ID
        StepperBlockProcessor._counter += 1
        stepper_id = f"lantern-stepper-{StepperBlockProcessor._counter}"
        id_match = re.search(r'id=(?:["\'])(.*?)(?:["\'])', args_str, re.IGNORECASE)
        if id_match:
            stepper_id = id_match.group(1).strip()

        # Extract blocks inside the directive with depth tracking
        accumulated = extract_directive_blocks(blocks)

        # Parse steps using STEP_SEP_RE
        steps: list[tuple[str, list[str]]] = []
        curr_title = ""
        curr_blocks: list[str] = []

        for blk in accumulated:
            lines = blk.splitlines()
            if lines and self.STEP_SEP_RE.match(lines[0].strip()):
                if curr_blocks or curr_title:
                    steps.append((curr_title or f"Phase {len(steps) + 1}", curr_blocks))
                    curr_blocks = []
                sep_match = self.STEP_SEP_RE.match(lines[0].strip())
                curr_title = (sep_match.group("title") or "").strip()
                if len(lines) > 1:
                    curr_blocks.append("\n".join(lines[1:]))
            else:
                curr_blocks.append(blk)

        if curr_blocks or curr_title:
            steps.append((curr_title or f"Phase {len(steps) + 1}", curr_blocks))

        if not steps:
            steps = [("Step 1", accumulated)]

        # Render Stepper HTML
        stepper = etree.SubElement(parent, "div")
        stepper.set("class", "lantern-stepper")
        stepper.set("id", stepper_id)
        stepper.set("data-active-step", "0")

        # Stepper Progress Header
        nav = etree.SubElement(stepper, "div")
        nav.set("class", "lantern-stepper-nav")

        for idx, (title, _) in enumerate(steps):
            btn = etree.SubElement(nav, "button")
            btn.set("class", f"lantern-stepper-btn{' active' if idx == 0 else ''}")
            btn.set("data-step-target", str(idx))

            num_span = etree.SubElement(btn, "span")
            num_span.set("class", "lantern-stepper-num")
            num_span.text = str(idx + 1)

            title_span = etree.SubElement(btn, "span")
            title_span.set("class", "lantern-stepper-title")
            title_span.text = title

        # Stepper Panes
        panes_container = etree.SubElement(stepper, "div")
        panes_container.set("class", "lantern-stepper-panes")

        for idx, (_, step_blocks) in enumerate(steps):
            pane = etree.SubElement(panes_container, "div")
            pane.set("class", f"lantern-stepper-pane{' active' if idx == 0 else ''}")
            pane.set("data-step-index", str(idx))
            if step_blocks:
                self.parser.parseBlocks(pane, step_blocks)

        # Stepper Controls
        controls = etree.SubElement(stepper, "div")
        controls.set("class", "lantern-stepper-controls")

        prev_btn = etree.SubElement(controls, "button")
        prev_btn.set("class", "lantern-btn lantern-btn-sm")
        prev_btn.set("data-stepper-action", "prev")
        prev_btn.text = "← Previous"

        readout = etree.SubElement(controls, "span")
        readout.set("class", "lantern-stepper-readout")
        readout.text = f"Step 1 of {len(steps)}"

        next_btn = etree.SubElement(controls, "button")
        next_btn.set("class", "lantern-btn lantern-btn-sm lantern-btn-primary")
        next_btn.set("data-stepper-action", "next")
        next_btn.text = "Next →"

        return True
