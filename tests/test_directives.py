"""Tests for custom Markdown directives (::: syntax)."""

from pathlib import Path
import pytest
from lantern.compiler import LanternCompiler


def test_callout_directive():
    compiler = LanternCompiler()
    md = """
::: callout type=warning title="Convergence Danger"
Watch out for non-positive-definite Hessians!
:::
"""
    html_out = compiler.compile(md)
    assert 'class="lantern-callout lantern-callout-warning"' in html_out
    assert "Convergence Danger" in html_out
    assert "Watch out for non-positive-definite Hessians!" in html_out


def test_canvas_walker_directive():
    compiler = LanternCompiler()
    md = """
::: canvas-walker landscape=ellipse algorithms=gd,newton
:::
"""
    html_out = compiler.compile(md)
    assert "lantern-walker-container" in html_out
    assert 'data-landscape="ellipse"' in html_out
    assert 'data-algorithms="gd,newton"' in html_out
    assert compiler.has_walker is True


def test_barrier_directive():
    compiler = LanternCompiler()
    md = """
::: barrier-vs-penalty
:::
"""
    html_out = compiler.compile(md)
    assert "lantern-barrier-container" in html_out
    assert "Barrier vs. Penalty Method Dynamics" in html_out
    assert compiler.has_barrier is True


def test_decision_ladder_directive():
    compiler = LanternCompiler()
    md = """
::: decision-ladder
:::
"""
    html_out = compiler.compile(md)
    assert "lantern-decision-container" in html_out
    assert "Algorithm & Strategy Decision Ladder" in html_out
    assert compiler.has_decision is True


def test_plot_directive_with_missing_script(tmp_path):
    compiler = LanternCompiler()
    md = """
::: plot non_existent.py backend=plotly
:::
"""
    html_out = compiler.compile(md, base_dir=tmp_path)
    assert "Plot Script Not Found" in html_out


def test_plot_directive_execution(tmp_path):
    # Create sample plotting script with self-contained figure exporter
    script = tmp_path / "test_plot.py"
    script.write_text(
        """
class MockFigure:
    def savefig(self, buf, **kwargs):
        buf.write("<svg viewBox='0 0 100 100'><circle cx='50' cy='50' r='40'/></svg>")

fig = MockFigure()
""",
        encoding="utf-8",
    )

    compiler = LanternCompiler()
    md = f"""
::: plot {script.name} backend=svg
:::
"""
    html_out = compiler.compile(md, base_dir=tmp_path)
    assert "lantern-plot-wrapper" in html_out
    assert script.name in html_out
    assert "<svg" in html_out or "Vector SVG" in html_out
    assert script in compiler.watched_scripts
