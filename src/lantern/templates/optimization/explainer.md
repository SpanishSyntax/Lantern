---
title: "Nonlinear Optimization & Algorithmic Convergence"
subtitle: "An Interactive Explainer on Gradient Dynamics, Curvature, and Constraint Relaxation"
author: "Frost Research Group"
template: explainer
snowpack_pdf: "report.pdf"
---

# Nonlinear Optimization Theory

Nonlinear optimization studies the minimization of a real-valued objective function $f: \mathbb{R}^n \to \mathbb{R}$:

$$\min_{x \in \mathcal{X}} f(x)$$

where $\mathcal{X} \subseteq \mathbb{R}^n$ denotes the feasible parameter space.

::: callout type=note title="Interactive Scientific Document"
This document is authored with **Lantern**, Frost's interactive compiler. It demonstrates multi-column spatial grids, real-time lab controls, Plotly surfaces, and KaTeX math.
:::

---

## 1. Landscape Geometry & 3D Manifolds

The classical benchmark for ill-conditioned curvature is the **Rosenbrock banana function**:

$$f(x_1, x_2) = (1 - x_1)^2 + 100(x_2 - x_1^2)^2$$

::: grid 60/40
=== Objective Manifold
::: plot plots/plot_rosenbrock.py backend=plotly height=480px title="Rosenbrock 3D Surface"
:::

=== Interactive Control Deck
::: card title="Curvature Diagnostics" badge="Ill-Conditioned" icon="📐"
Near the global minimum $x^* = (1, 1)$, the condition number $\kappa(H) = \frac{\lambda_{\max}}{\lambda_{\min}} \gg 100$, producing intense oscillations in standard first-order algorithms.

::: slider id="step-size" label="Learning Rate α" min="0.0001" max="0.01" step="0.0005" default="0.002" unit="s"
:::

::: switch id="momentum-toggle" label="Enable Polyak Momentum" default=true
:::

::: segments id="landscape-picker" default="rosenbrock"
- [rosenbrock]: Rosenbrock
- [ellipse]: Ellipse (κ=20)
- [rastrigin]: Rastrigin
- [saddle]: Saddle
:::
:::
:::

---

## 2. Convergence Analysis & Method Comparison

::: comparison
=== Left: First-Order Gradient Descent
- **Memory Complexity:** $O(n)$
- **Per-Iteration Cost:** $O(n)$ gradient evaluations
- **Convergence Rate:** Linear $O(1/k)$
- **Sensitivity:** Pathological zig-zagging in anisotropic valleys

=== Right: Second-Order Newton-Raphson
- **Memory Complexity:** $O(n^2)$ for Hessian matrix $H(x)$
- **Per-Iteration Cost:** $O(n^3)$ linear system solve $H \Delta x = -\nabla f$
- **Convergence Rate:** Quadratic $\|x_{k+1} - x^*\| \le M \|x_k - x^*\|^2$
- **Sensitivity:** Requires positive-definite Hessian regularization
:::

::: metrics cols=4
- Iterations to Optimum: 42
- Final Loss f(x*): 0.0000 [badge=emerald]
- Gradient Norm ‖∇f‖: 8.4e-6
- Convergence Status: Verified [badge=cyan]
:::

---

## 3. Algorithmic Workflow

::: stepper id="opt-stepper"
=== Step 1: Gradient Evaluation
Evaluate gradient vector $g_k = \nabla f(x_k)$. Verify termination criterion $\|g_k\| < \epsilon$.

=== Step 2: Search Direction Computation
Compute descent vector $d_k = -B_k^{-1} g_k$ using exact Newton or quasi-Newton BFGS updates.

=== Step 3: Armijo Line Search
Select step length $\alpha_k$ satisfying the sufficient decrease condition:
$$f(x_k + \alpha_k d_k) \le f(x_k) + c_1 \alpha_k g_k^T d_k$$

=== Step 4: Parameter Update
Step to next point $x_{k+1} = x_k + \alpha_k d_k$ and update inverse Hessian approximation $B_{k+1}$.
:::

---

## 4. Deep Mathematical Proofs

::: accordion title="Proof of Quadratic Convergence for Pure Newton-Raphson"
Assume $f \in C^2$ is strongly convex and the Hessian $H(x)$ is Lipschitz continuous with constant $L$:

$$\|H(x) - H(y)\| \le L \|x - y\|$$

Expanding the gradient about $x^*$ using Taylor's theorem:

$$\nabla f(x_k) = \nabla f(x^*) + \int_0^1 H(x^* + t(x_k - x^*))(x_k - x^*) dt$$

Since $\nabla f(x^*) = 0$ at the stationary point, substituting the Newton step $x_{k+1} = x_k - H(x_k)^{-1} \nabla f(x_k)$ leads to:

$$\|x_{k+1} - x^*\| \le \frac{1}{2} L \|H(x_k)^{-1}\| \|x_k - x^*\|^2$$

demonstrating asymptotic second-order quadratic convergence.
:::

---

## 5. Multi-Perspective Lab Tabs

::: tabs
=== Intuition
Imagine navigating a dense fog down a mountain. Gradient descent looks solely at the steepest slope under your boots, causing you to slide back and forth across a canyon floor. Newton-Raphson fits a parabolic bowl to the terrain, estimating where the valley floor actually terminates.

=== Formulation
The exact update equations are:

$$\text{GD:} \quad x_{k+1} = x_k - \alpha \nabla f(x_k)$$

$$\text{Newton:} \quad x_{k+1} = x_k - [H(x_k) + \mu I]^{-1} \nabla f(x_k)$$

$$\text{BFGS:} \quad B_{k+1} = (I - \rho_k s_k y_k^T) B_k (I - \rho_k y_k s_k^T) + \rho_k s_k s_k^T$$

=== Transport Simulation
::: player id="sim-player" target="trajectory-view" speeds="0.5x, 1x, 2x, 5x"
:::
:::
