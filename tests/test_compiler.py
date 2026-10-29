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


def test_math_restoration_large():
    compiler = LanternCompiler()
    # Generate 500 inline and 500 display math expressions
    lines = ["# Large Math Benchmark Document\n"]
    for i in range(500):
        lines.append(f"Inline eq {i}: $f_{i}(x) = x_{i}^2 + \\alpha_{i} x$ and display:")
        lines.append(f"$$\\int_{{0}}^{{\\infty}} e^{{-{i} t}} dt = \\frac{{1}}{{{i + 1}}}$$")
    doc = "\n".join(lines)
    html_out = compiler.compile(doc, standalone=False)
    assert "$f_0(x) = x_0^2 + \\alpha_0 x$" in html_out
    assert "$f_499(x) = x_499^2 + \\alpha_499 x$" in html_out
    assert "KATEXDISPLAYMATHPLACEHOLDER" not in html_out
    assert "KATEXINLINEMATHPLACEHOLDER" not in html_out


def test_export_static(tmp_path):
    compiler = LanternCompiler()
    doc_path = tmp_path / "test_doc.md"
    doc_path.write_text("# Test Document\n\nSome content with math $x^2$ here.\n", encoding="utf-8")
    out_dir = tmp_path / "static_bundle"
    res_dir = compiler.export_static(doc_path, output_dir=out_dir)

    assert res_dir == out_dir
    assert (out_dir / "index.html").exists()
    assert (out_dir / "static" / "lantern.css").exists()
    assert (out_dir / "static" / "lantern.js").exists()
    assert (out_dir / "README.md").exists()

    readme_text = (out_dir / "README.md").read_text(encoding="utf-8")
    assert "Caddy Server" in readme_text


def test_export_jinja(tmp_path):
    compiler = LanternCompiler()
    doc_path = tmp_path / "test_doc.md"
    doc_path.write_text("# Test Document\n\nContent for Jinja server.\n", encoding="utf-8")
    out_dir = tmp_path / "jinja_bundle"
    res_dir = compiler.export_jinja(doc_path, output_dir=out_dir)

    assert res_dir == out_dir
    assert (out_dir / "app.py").exists()
    assert (out_dir / "requirements.txt").exists()
    assert (out_dir / "Dockerfile").exists()
    assert (out_dir / "templates" / "base.html.j2").exists()
    assert (out_dir / "content" / "test_doc.md").exists()
    assert (out_dir / "static" / "lantern.css").exists()
    assert (out_dir / "README.md").exists()

    app_py_text = (out_dir / "app.py").read_text(encoding="utf-8")
    assert "def app(environ" in app_py_text
    assert "gunicorn" in (out_dir / "requirements.txt").read_text(encoding="utf-8")
