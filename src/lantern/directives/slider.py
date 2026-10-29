"""Slider directive for continuous numerical parameter exploration (::: slider ...)."""

from __future__ import annotations

import re
from typing import Any
import xml.etree.ElementTree as etree
from markdown.blockprocessors import BlockProcessor


class SliderBlockProcessor(BlockProcessor):
    """Processes ::: slider id="..." label="..." min=... max=... step=... default=... [unit="..."] blocks."""

    START_RE = re.compile(
        r"^:::\s*slider(?:\s+(?P<args>.*))?$",
        re.IGNORECASE,
    )
    END_RE = re.compile(r"^:::\s*$")

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

        # Parse parameters
        SliderBlockProcessor._counter += 1
        slider_id = f"slider-{SliderBlockProcessor._counter}"
        label = "Parameter"
        min_val = "0"
        max_val = "1"
        step = "0.01"
        default_val = "0.5"
        unit = ""

        def extract_arg(param: str, default: str) -> str:
            m = re.search(r'\b' + param + r'=(?:["\'])(.*?)(?:["\'])', args_str, re.IGNORECASE)
            if not m:
                m = re.search(r'\b' + param + r'=([^\s]+)', args_str, re.IGNORECASE)
            return m.group(1).strip() if m else default

        slider_id = extract_arg("id", slider_id)
        label = extract_arg("label", label)
        min_val = extract_arg("min", min_val)
        max_val = extract_arg("max", max_val)
        step = extract_arg("step", step)
        default_val = extract_arg("default", min_val)
        unit = extract_arg("unit", unit)

        # Consume blocks if multiline directive
        blocks.pop(0)
        while blocks:
            blk = blocks[0].strip()
            if self.END_RE.match(blk):
                blocks.pop(0)
                break
            break

        # Render Slider HTML
        wrap = etree.SubElement(parent, "div")
        wrap.set("class", "lantern-control-wrap lantern-control-slider")
        wrap.set("data-control-id", slider_id)

        header = etree.SubElement(wrap, "div")
        header.set("class", "lantern-slider-header")

        lbl_el = etree.SubElement(header, "label")
        lbl_el.set("class", "lantern-control-label")
        lbl_el.set("for", f"ctrl-{slider_id}")
        lbl_el.text = label

        val_el = etree.SubElement(header, "span")
        val_el.set("class", "lantern-slider-val")
        val_el.set("id", f"val-{slider_id}")
        val_el.text = f"{default_val}{unit}"

        input_el = etree.SubElement(wrap, "input")
        input_el.set("type", "range")
        input_el.set("class", "lantern-slider")
        input_el.set("id", f"ctrl-{slider_id}")
        input_el.set("name", slider_id)
        input_el.set("min", min_val)
        input_el.set("max", max_val)
        input_el.set("step", step)
        input_el.set("value", default_val)
        input_el.set("data-unit", unit)

        return True
