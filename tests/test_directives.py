"""Comprehensive tests for Lantern's 3 component directive families."""

from pathlib import Path
import pytest
from lantern.compiler import LanternCompiler


# =========================================================================
# Family 1: Layout & Spatial Chrome Tests
# =========================================================================

def test_grid_directive_presets():
    compiler = LanternCompiler()

    # 50/50 preset
    md_50 = """
::: grid 50/50
=== Left Col
Left text

=== Right Col
Right text
:::
"""
    html_50 = compiler.compile(md_50)
    assert 'class="lantern-grid-strip"' in html_50
    assert "grid-template-columns: 1fr 1fr;" in html_50
    assert "Left Col" in html_50
    assert "Right Col" in html_50

    # 60/40 preset
    md_60 = """
::: grid 60/40
=== Plot Side
Plot info

=== Controls Side
Control info
:::
"""
    html_60 = compiler.compile(md_60)
    assert "grid-template-columns: 1.5fr 1fr;" in html_60

    # 3-col preset
    md_3 = """
::: grid 3-col
=== Col 1
1

=== Col 2
2

=== Col 3
3
:::
"""
    html_3 = compiler.compile(md_3)
    assert "grid-template-columns: repeat(3, 1fr);" in html_3


def test_card_directive():
    compiler = LanternCompiler()
    md = """
::: card title="Active Set QP" badge="Convex" icon="💎"
A single smooth quadratic bowl with polyhedral constraints.
:::
"""
    html_out = compiler.compile(md)
    assert 'class="lantern-card"' in html_out
    assert "Active Set QP" in html_out
    assert "Convex" in html_out
    assert "💎" in html_out
    assert "polyhedral constraints" in html_out


def test_stepper_directive():
    compiler = LanternCompiler()
    md = """
::: stepper id="simplex-flow"
=== Step 1: Reduced Costs
Compute pricing vector.

=== Step 2: Ratio Test
Determine pivot element.
:::
"""
    html_out = compiler.compile(md)
    assert 'class="lantern-stepper"' in html_out
    assert 'id="simplex-flow"' in html_out
    assert "Reduced Costs" in html_out
    assert "Ratio Test" in html_out
    assert "lantern-stepper-btn" in html_out
    assert "lantern-stepper-pane" in html_out


def test_curtain_directive():
    compiler = LanternCompiler()
    md = """
::: curtain
=== Before: Vanilla Descent
Oscillating wildly.

=== After: Newton Damping
Quadratic convergence.
:::
"""
    html_out = compiler.compile(md)
    assert 'class="lantern-curtain"' in html_out
    assert "Vanilla Descent" in html_out
    assert "Newton Damping" in html_out


# =========================================================================
# Family 2: Interactive Controls & Lab Inputs Tests
# =========================================================================

def test_slider_directive():
    compiler = LanternCompiler()
    md = """
::: slider id="step-alpha" label="Step Size α" min="0.001" max="0.1" step="0.005" default="0.02" unit="s"
:::
"""
    html_out = compiler.compile(md)
    assert 'class="lantern-control-wrap lantern-control-slider"' in html_out
    assert 'data-control-id="step-alpha"' in html_out
    assert 'id="val-step-alpha"' in html_out
    assert "0.02s" in html_out
    assert 'min="0.001"' in html_out
    assert 'max="0.1"' in html_out


def test_switch_directive():
    compiler = LanternCompiler()
    md = """
::: switch id="momentum-toggle" label="Enable Momentum" default=true
:::
"""
    html_out = compiler.compile(md)
    assert 'class="lantern-control-wrap lantern-control-switch"' in html_out
    assert 'data-control-id="momentum-toggle"' in html_out
    assert "Enable Momentum" in html_out
    assert 'checked="checked"' in html_out


def test_segments_directive():
    compiler = LanternCompiler()
    md = """
::: segments id="solver" default="bfgs"
- [gd]: Gradient Descent
- [bfgs]: Quasi-Newton BFGS
- [newton]: Exact Newton
:::
"""
    html_out = compiler.compile(md)
    assert 'class="lantern-control-wrap lantern-control-segments"' in html_out
    assert 'data-control-id="solver"' in html_out
    assert 'data-val="bfgs"' in html_out
    assert 'class="lantern-segment-btn active"' in html_out
    assert 'value="bfgs"' in html_out


def test_select_directive():
    compiler = LanternCompiler()
    md = """
::: select id="terrain" label="Objective Manifold" default="ellipse"
- [rosenbrock]: Rosenbrock Valley
- [ellipse]: Ill-Conditioned Ellipse
:::
"""
    html_out = compiler.compile(md)
    assert 'class="lantern-control-wrap lantern-control-select"' in html_out
    assert 'data-control-id="terrain"' in html_out
    assert 'value="ellipse"' in html_out
    assert 'selected="selected"' in html_out


def test_player_directive():
    compiler = LanternCompiler()
    md = """
::: player id="ode-player" target="phase-canvas" speeds="0.5x, 1x, 2x"
:::
"""
    html_out = compiler.compile(md)
    assert 'class="lantern-player"' in html_out
    assert 'id="ode-player"' in html_out
    assert 'data-target="phase-canvas"' in html_out
    assert 'data-player-action="play"' in html_out
    assert 'data-player-action="reset"' in html_out


# =========================================================================
# Family 3: Editorial Content & Feedback Tests
# =========================================================================

def test_metrics_directive():
    compiler = LanternCompiler()
    md = """
::: metrics cols=3
- Loss: 0.0042 [badge=emerald]
- Iterations: 85
- Status: Converged [badge=cyan]
:::
"""
    html_out = compiler.compile(md)
    assert 'class="lantern-metrics-deck"' in html_out
    assert "Loss" in html_out
    assert "0.0042" in html_out
    assert "lantern-badge-emerald" in html_out
    assert "Iterations" in html_out
    assert "85" in html_out


def test_tabs_directive():
    compiler = LanternCompiler()
    md = """
::: tabs id="theory-tabs"
=== Formulation
Equation: $f(x) = x^2$

=== Proof
By convexity.
:::
"""
    html_out = compiler.compile(md)
    assert 'class="lantern-tabs"' in html_out
    assert 'id="theory-tabs"' in html_out
    assert "Formulation" in html_out
    assert "Proof" in html_out
    assert "lantern-tab-btn" in html_out
    assert "lantern-tab-pane" in html_out


def test_accordion_directive():
    compiler = LanternCompiler()
    md = """
::: accordion title="Lipschitz Continuous Proof" open
Hessian bounds hold globally.
:::
"""
    html_out = compiler.compile(md)
    assert 'class="lantern-accordion"' in html_out
    assert 'open="open"' in html_out
    assert "Lipschitz Continuous Proof" in html_out
    assert "Hessian bounds hold globally." in html_out


def test_comparison_directive():
    compiler = LanternCompiler()
    md = """
::: comparison
=== Left: First-Order
Linear speed.

=== Right: Second-Order
Quadratic speed.
:::
"""
    html_out = compiler.compile(md)
    assert 'class="lantern-comparison"' in html_out
    assert "lantern-comparison-left" in html_out
    assert "lantern-comparison-right" in html_out
    assert "Linear speed." in html_out
    assert "Quadratic speed." in html_out


def test_callout_directive():
    compiler = LanternCompiler()
    md = """
::: callout type=warning title="Indefinite Matrix"
Non-positive curvature detected!
:::
"""
    html_out = compiler.compile(md)
    assert 'class="lantern-callout lantern-callout-warning"' in html_out
    assert "Indefinite Matrix" in html_out
    assert "Non-positive curvature detected!" in html_out


def test_tooltip_inline_processor():
    compiler = LanternCompiler()
    md = "The [?Hessian: Matrix of second-order partial derivatives] governs local curvature."
    html_out = compiler.compile(md)
    assert 'class="lantern-tooltip"' in html_out
    assert 'data-tooltip="Matrix of second-order partial derivatives"' in html_out
    assert "Hessian" in html_out


def test_plot_directive_with_lightbox(tmp_path):
    script = tmp_path / "plot_fig.py"
    script.write_text(
        """
class MockFig:
    def savefig(self, buf, **kwargs):
        buf.write("<svg viewBox='0 0 100 100'><circle cx='50' cy='50' r='30'/></svg>")

fig = MockFig()
""",
        encoding="utf-8",
    )

    compiler = LanternCompiler()
    md = f"""
::: plot {script.name} backend=svg title="Vector Figure"
:::
"""
    html_out = compiler.compile(md, base_dir=tmp_path)
    assert "lantern-plot-wrapper" in html_out
    assert "Vector Figure" in html_out
    assert "lantern-lightbox-trigger" in html_out
    assert "<svg" in html_out


def test_plot_directive_auto_injects_uirevision(tmp_path):
    script = tmp_path / "plot_plotly.py"
    script.write_text(
        """
class MockLayout:
    uirevision = None

class MockPlotlyFig:
    def __init__(self):
        self.layout = MockLayout()
    def to_html(self, **kwargs):
        return f"<div class='plotly-graph-div' data-uirevision='{self.layout.uirevision}'></div>"

fig = MockPlotlyFig()
""",
        encoding="utf-8",
    )

    compiler = LanternCompiler()
    md = f"""
::: plot {script.name} backend=plotly title="Auto UIRevision Plot"
:::
"""
    html_out = compiler.compile(md, base_dir=tmp_path)
    assert "lantern-plot-wrapper" in html_out
    assert "data-uirevision='lantern-persist'" in html_out
