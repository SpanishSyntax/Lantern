"""Player directive for simulation media playback and time stepping (::: player ...)."""

from __future__ import annotations

import re
from typing import Any
import xml.etree.ElementTree as etree
from markdown.blockprocessors import BlockProcessor


class PlayerBlockProcessor(BlockProcessor):
    """Processes ::: player id="..." [target="..."] [speeds="..."] blocks."""

    START_RE = re.compile(
        r"^:::\s*player(?:\s+(?P<args>.*))?$",
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

        PlayerBlockProcessor._counter += 1
        player_id = f"player-{PlayerBlockProcessor._counter}"
        target = ""
        speeds = "0.5x, 1x, 2x, 5x"

        def extract_arg(param: str, default: str) -> str:
            m = re.search(r'\b' + param + r'=(?:["\'])(.*?)(?:["\'])', args_str, re.IGNORECASE)
            if not m:
                m = re.search(r'\b' + param + r'=([^\s]+)', args_str, re.IGNORECASE)
            return m.group(1).strip() if m else default

        player_id = extract_arg("id", player_id)
        target = extract_arg("target", target)
        speeds = extract_arg("speeds", speeds)

        # Consume blocks if multiline directive
        blocks.pop(0)
        while blocks:
            blk = blocks[0].strip()
            if self.END_RE.match(blk):
                blocks.pop(0)
                break
            break

        speed_list = [s.strip() for s in speeds.split(",") if s.strip()]
        if not speed_list:
            speed_list = ["1x"]

        # Render Player HTML
        player = etree.SubElement(parent, "div")
        player.set("class", "lantern-player")
        player.set("id", player_id)
        if target:
            player.set("data-target", target)

        controls = etree.SubElement(player, "div")
        controls.set("class", "lantern-player-controls")

        btn_group = etree.SubElement(controls, "div")
        btn_group.set("class", "lantern-player-btn-group")

        reset_btn = etree.SubElement(btn_group, "button")
        reset_btn.set("class", "lantern-btn lantern-btn-sm")
        reset_btn.set("data-player-action", "reset")
        reset_btn.text = "⏮ Reset"

        play_btn = etree.SubElement(btn_group, "button")
        play_btn.set("class", "lantern-btn lantern-btn-sm lantern-btn-primary")
        play_btn.set("data-player-action", "play")
        play_btn.text = "⏵ Play"

        step_btn = etree.SubElement(btn_group, "button")
        step_btn.set("class", "lantern-btn lantern-btn-sm")
        step_btn.set("data-player-action", "step")
        step_btn.text = "⏭ Step"

        # Speed selector
        speed_wrap = etree.SubElement(controls, "div")
        speed_wrap.set("class", "lantern-player-speed-wrap")
        speed_sel = etree.SubElement(speed_wrap, "select")
        speed_sel.set("class", "lantern-select lantern-select-sm")
        speed_sel.set("data-player-control", "speed")

        for spd in speed_list:
            opt = etree.SubElement(speed_sel, "option")
            opt.set("value", spd.replace("x", ""))
            if spd == "1x":
                opt.set("selected", "selected")
            opt.text = spd

        # Scrubber / Timeline
        scrubber_wrap = etree.SubElement(player, "div")
        scrubber_wrap.set("class", "lantern-player-scrubber-wrap")

        scrubber = etree.SubElement(scrubber_wrap, "input")
        scrubber.set("type", "range")
        scrubber.set("class", "lantern-slider lantern-player-scrubber")
        scrubber.set("data-player-control", "scrubber")
        scrubber.set("min", "0")
        scrubber.set("max", "100")
        scrubber.set("value", "0")

        badge = etree.SubElement(scrubber_wrap, "span")
        badge.set("class", "lantern-player-frame-badge")
        badge.text = "t = 0 / 100"

        return True
