"""Lantern custom markdown directives extension."""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any
from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor
import xml.etree.ElementTree as etree

from lantern.directives.accordion import AccordionBlockProcessor
from lantern.directives.callout import CalloutBlockProcessor
from lantern.directives.card import CardBlockProcessor
from lantern.directives.comparison import ComparisonBlockProcessor
from lantern.directives.curtain import CurtainBlockProcessor
from lantern.directives.grid import GridBlockProcessor
from lantern.directives.metrics import MetricsBlockProcessor
from lantern.directives.player import PlayerBlockProcessor
from lantern.directives.plot import PlotBlockProcessor
from lantern.directives.segments import SegmentsBlockProcessor
from lantern.directives.select import SelectBlockProcessor
from lantern.directives.slider import SliderBlockProcessor
from lantern.directives.stepper import StepperBlockProcessor
from lantern.directives.switch import SwitchBlockProcessor
from lantern.directives.tabs import TabsBlockProcessor


class TooltipInlineProcessor(InlineProcessor):
    """Processes [?term: definition text] into hover tooltips."""

    def handleMatch(self, m: re.Match[str], data: str) -> tuple[etree.Element, int, int]:
        term = m.group("term").strip()
        defn = m.group("def").strip()

        el = etree.Element("span")
        el.set("class", "lantern-tooltip")
        el.set("data-tooltip", defn)
        el.text = term

        return el, m.start(0), m.end(0)


class LanternExtension(Extension):
    """Python-Markdown extension registering Frost/Lantern scientific directives."""

    def __init__(self, compiler: Any = None, base_dir: Path | None = None, **kwargs: Any) -> None:
        self.compiler = compiler
        self.base_dir = base_dir
        super().__init__(**kwargs)

    def extendMarkdown(self, md: Any) -> None:
        # Register block processors with priorities above standard paragraphs (100)
        md.parser.blockprocessors.register(CalloutBlockProcessor(md.parser), "lantern_callout", 120)
        md.parser.blockprocessors.register(GridBlockProcessor(md.parser), "lantern_grid", 119)
        md.parser.blockprocessors.register(CardBlockProcessor(md.parser), "lantern_card", 118)
        md.parser.blockprocessors.register(TabsBlockProcessor(md.parser), "lantern_tabs", 117)
        md.parser.blockprocessors.register(AccordionBlockProcessor(md.parser), "lantern_accordion", 116)
        md.parser.blockprocessors.register(ComparisonBlockProcessor(md.parser), "lantern_comparison", 115)
        md.parser.blockprocessors.register(StepperBlockProcessor(md.parser), "lantern_stepper", 114)
        md.parser.blockprocessors.register(CurtainBlockProcessor(md.parser), "lantern_curtain", 113)
        md.parser.blockprocessors.register(MetricsBlockProcessor(md.parser), "lantern_metrics", 112)
        md.parser.blockprocessors.register(
            PlotBlockProcessor(md.parser, compiler=self.compiler, base_dir=self.base_dir),
            "lantern_plot",
            111,
        )
        md.parser.blockprocessors.register(SliderBlockProcessor(md.parser), "lantern_slider", 110)
        md.parser.blockprocessors.register(SwitchBlockProcessor(md.parser), "lantern_switch", 109)
        md.parser.blockprocessors.register(SegmentsBlockProcessor(md.parser), "lantern_segments", 108)
        md.parser.blockprocessors.register(SelectBlockProcessor(md.parser), "lantern_select", 107)
        md.parser.blockprocessors.register(PlayerBlockProcessor(md.parser), "lantern_player", 106)

        # Register inline tooltip processor [?term: definition text]
        TOOLTIP_PATTERN = r"\[\?(?P<term>[^:\n]+):\s*(?P<def>[^\]\n]+)\]"
        md.inlinePatterns.register(TooltipInlineProcessor(TOOLTIP_PATTERN, md), "lantern_tooltip", 175)


__all__ = [
    "LanternExtension",
    "CalloutBlockProcessor",
    "GridBlockProcessor",
    "CardBlockProcessor",
    "TabsBlockProcessor",
    "AccordionBlockProcessor",
    "ComparisonBlockProcessor",
    "StepperBlockProcessor",
    "CurtainBlockProcessor",
    "MetricsBlockProcessor",
    "PlotBlockProcessor",
    "SliderBlockProcessor",
    "SwitchBlockProcessor",
    "SegmentsBlockProcessor",
    "SelectBlockProcessor",
    "PlayerBlockProcessor",
    "TooltipInlineProcessor",
]
