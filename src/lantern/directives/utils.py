"""Directive utility functions, including depth-aware block extraction."""

from __future__ import annotations

import re

DIRECTIVE_START_RE = re.compile(r"^:::\s*([a-zA-Z0-9_\-]+)", re.IGNORECASE)
DIRECTIVE_END_RE = re.compile(r"^:::\s*$")


def extract_directive_blocks(blocks: list[str]) -> list[str]:
    """
    Extracts all Markdown blocks belonging to a multi-line container directive,
    correctly tracking nested directive depth.

    Opening tags (e.g. `::: card`, `::: grid`) increment depth.
    Closing tags (`:::`) decrement depth.
    Consumes matching blocks from the input `blocks` list in-place.
    """
    if not blocks:
        return []

    first_block = blocks.pop(0)
    lines = first_block.strip().splitlines()
    first_block_rest = "\n".join(lines[1:]) if len(lines) > 1 else ""

    accumulated: list[str] = []
    depth = 1

    if first_block_rest.strip():
        # Check if first_block_rest contains opening or closing directives
        for rest_line in first_block_rest.splitlines():
            s = rest_line.strip()
            if DIRECTIVE_START_RE.match(s):
                depth += 1
            elif DIRECTIVE_END_RE.match(s):
                depth -= 1
                if depth == 0:
                    break
        accumulated.append(first_block_rest)
        if depth == 0:
            return accumulated

    while blocks:
        blk = blocks.pop(0)
        blk_lines = blk.splitlines()

        stop_index: int | None = None
        for i, line in enumerate(blk_lines):
            s = line.strip()
            if DIRECTIVE_START_RE.match(s):
                depth += 1
            elif DIRECTIVE_END_RE.match(s):
                depth -= 1
                if depth == 0:
                    stop_index = i
                    break

        if stop_index is not None:
            # Reached depth 0 (closing tag for this directive)
            if stop_index > 0:
                accumulated.append("\n".join(blk_lines[:stop_index]))
            # If there are lines remaining after closing :::, push back to blocks
            remaining = blk_lines[stop_index + 1 :]
            if remaining:
                blocks.insert(0, "\n".join(remaining))
            break
        else:
            accumulated.append(blk)

    return accumulated
