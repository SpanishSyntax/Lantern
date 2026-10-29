"""Tests for Lantern compiler, frontmatter parsing, and math preservation."""

import pytest
from lantern.compiler import LanternCompiler


def test_frontmatter_parsing():
    compiler = LanternCompiler()
    doc = """---
title: "Optimization Deep Dive"
author: "Frost Team"
standalone: true
---
# Main Heading
Some text here.
"""
    fm, content = compiler.parse_frontmatter(doc)
    assert fm["title"] == "Optimization Deep Dive"
    assert fm["author"] == "Frost Team"
    assert fm["standalone"] is True
    assert "# Main Heading" in content


def test_title_fallback():
    compiler = LanternCompiler()
    doc = """# Gradient Descent Convergence
This is an explainer.
"""
    fm, content = compiler.parse_frontmatter(doc)
    title = compiler.extract_title(content)
    assert title == "Gradient Descent Convergence"


def test_math_protection():
    compiler = LanternCompiler()
    # Math containing underscores that would normally be converted to <em> by markdown
    text = "Let $x_k^* = \\arg\\min_{x} f(x)$ and $$\\sum_{i=1}^n x_i^2 \\le 1$$"
    html_out = compiler.compile(text, standalone=False)
    # Ensure raw KaTeX delimiters are preserved
    assert "$x_k^* = \\arg\\min_{x} f(x)$" in html_out
    assert "$$\\sum_{i=1}^n x_i^2 \\le 1$$" in html_out
    # Ensure underscores were not replaced with <em>
    assert "<em>" not in html_out


def test_standalone_compilation():
    compiler = LanternCompiler()
    doc = """# Title
::: callout type=tip
Helpful tip!
:::
"""
    html_out = compiler.compile(doc, standalone=True)
    assert "<style>" in html_out
    assert "Obsidian Frost" in html_out
    assert "Helpful tip!" in html_out
