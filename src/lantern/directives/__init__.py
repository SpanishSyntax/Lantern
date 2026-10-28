"""Lantern custom markdown directives extension."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from markdown.extensions import Extension

from lantern.directives.barrier import BarrierBlockProcessor
from lantern.directives.callout import CalloutBlockProcessor
from lantern.directives.decision import DecisionLadderBlockProcessor
from lantern.directives.plot import PlotBlockProcessor
from lantern.directives.walker import CanvasWalkerBlockProcessor


class LanternExtension(Extension):
    """Python-Markdown extension registering Frost/Lantern custom ::: directives."""

    def __init__(self, compiler: Any = None, base_dir: Path | None = None, **kwargs: Any) -> None:
        self.compiler = compiler
        self.base_dir = base_dir
        super().__init__(**kwargs)

    def extendMarkdown(self, md: Any) -> None:
        # Register block processors with high priority (e.g. 105)
        md.parser.blockprocessors.register(
            CalloutBlockProcessor(md.parser), "lantern_callout", 110
        )
        md.parser.blockprocessors.register(
            PlotBlockProcessor(md.parser, compiler=self.compiler, base_dir=self.base_dir),
            "lantern_plot",
            109,
        )
        md.parser.blockprocessors.register(
            CanvasWalkerBlockProcessor(md.parser, compiler=self.compiler),
            "lantern_walker",
            108,
        )
        md.parser.blockprocessors.register(
            BarrierBlockProcessor(md.parser, compiler=self.compiler),
            "lantern_barrier",
            107,
        )
        md.parser.blockprocessors.register(
            DecisionLadderBlockProcessor(md.parser, compiler=self.compiler, base_dir=self.base_dir),
            "lantern_decision",
            106,
        )


__all__ = [
    "LanternExtension",
    "CalloutBlockProcessor",
    "PlotBlockProcessor",
    "CanvasWalkerBlockProcessor",
    "BarrierBlockProcessor",
    "DecisionLadderBlockProcessor",
]
