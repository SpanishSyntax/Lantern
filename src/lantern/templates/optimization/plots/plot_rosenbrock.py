"""Sample Barograph Plotting Script: Rosenbrock Valley Optimization Landscape."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

# 2D Grid over Rosenbrock domain
x = np.linspace(-2.0, 2.0, 100)
y = np.linspace(-1.0, 3.0, 100)
X, Y = np.meshgrid(x, y)
Z = (1.0 - X) ** 2 + 100.0 * (Y - X ** 2) ** 2
Z_log = np.log10(Z + 1.0)

fig = go.Figure()

# 3D Log-surface
fig.add_trace(
    go.Surface(
        x=X,
        y=Y,
        z=Z_log,
        colorscale="Viridis",
        showscale=False,
        opacity=0.92,
        contours=dict(
            z=dict(show=True, usecolormap=True, highlightcolor="#38bdf8", project_z=True)
        ),
    )
)

# Global minimizer marker at (1, 1, 0)
fig.add_trace(
    go.Scatter3d(
        x=[1.0],
        y=[1.0],
        z=[0.0],
        mode="markers+text",
        marker=dict(size=7, color="#34d399", symbol="diamond"),
        text=["Global Optimum x* (1.0, 1.0)"],
        textposition="top center",
        name="Optimum",
    )
)

fig.update_layout(
    title=dict(
        text="Rosenbrock Valley Objective Manifold $\\log_{10}(f(x, y) + 1)$",
        font=dict(size=14, color="#f8fafc"),
    ),
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    scene=dict(
        xaxis=dict(title="x₁", backgroundcolor="#0b0f17", gridcolor="#1e293b", color="#94a3b8"),
        yaxis=dict(title="x₂", backgroundcolor="#0b0f17", gridcolor="#1e293b", color="#94a3b8"),
        zaxis=dict(title="log₁₀(f+1)", backgroundcolor="#0b0f17", gridcolor="#1e293b", color="#94a3b8"),
        camera=dict(eye=dict(x=-1.5, y=-1.5, z=1.2)),
    ),
    margin=dict(l=0, r=0, t=40, b=0),
)
