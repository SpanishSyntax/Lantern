---
title: "Nonlinear Optimization & Algorithmic Convergence"
subtitle: "An Interactive Explainer on Gradient Dynamics, Curvature, and Constraint Relaxation"
author: "Frost Research Group"
template: explainer
---

# Mathematical Foundations

Nonlinear optimization concerns the minimization of a continuously differentiable objective function $f: \mathbb{R}^n \to \mathbb{R}$:

$$\min_{x \in \mathcal{X}} f(x)$$

where the feasible region $\mathcal{X} \subseteq \mathbb{R}^n$ may be unconstrained ($\mathcal{X} = \mathbb{R}^n$) or defined through nonlinear inequality constraints $g_i(x) \le 0$.

::: callout type=note title="Frost Interactive Compiler"
This document is compiled using **Lantern**, Frost's zero-dependency compiler for interactive explainers and simulation dashboards. All KaTeX math ($...$ and $$...$$), canvas simulations, and Plotly graphics are fully rendered client-side.
:::

---

## 1. Objective Geometry & Curvature

The classical benchmark for unconstrained numerical optimization is the **Rosenbrock banana function**:

$$f(x_1, x_2) = (1 - x_1)^2 + 100(x_2 - x_1^2)^2$$

The global minimum lies inside a steep, parabolic valley at $x^* = (1, 1)^T$ where $f(x^*) = 0$. Computing the gradient $\nabla f(x)$ yields:

$$\nabla f(x) = \begin{bmatrix} -2(1 - x_1) - 400x_1(x_2 - x_1^2) \\ 200(x_2 - x_1^2) \end{bmatrix}$$

The exact symmetric Hessian matrix $H(x) = \nabla^2 f(x)$ is:

$$H(x) = \begin{bmatrix} 2 - 400(x_2 - 3x_1^2) & -400x_1 \\ -400x_1 & 200 \end{bmatrix}$$

At the bottom of the valley, the condition number $\kappa(H) = \frac{\lambda_{\max}}{\lambda_{\min}} \gg 1$, producing severe oscillations for standard first-order gradient descent.

Below is the live 3D surface rendered by `plot_optimization.py`:

::: plot plot_optimization.py backend=plotly height=520px
:::

---

## 2. Interactive Algorithmic Walker

Explore algorithmic convergence dynamics in real time. Compare **Gradient Descent**, **Armijo Backtracking**, **Newton-Raphson**, **Quasi-Newton BFGS**, and **Polyak Momentum**.

::: callout type=tip title="Interactive Trajectory Seeding"
Click or drag anywhere on the high-DPI canvas to pick the initial coordinate $(x_0, y_0)$. Observe how second-order Newton steps jump across anisotropic valleys while standard GD oscillates orthogonal to the contour walls.
:::

::: canvas-walker landscape=rosenbrock algorithms=gd,armijo,newton,bfgs,momentum
:::

---

## 3. Constraint Relaxation: Barrier vs. Penalty

When inequality constraints $g(x) \le 0$ are active, we approximate the constrained problem via parametric unconstrained subproblems:

### Quadratic Exterior Penalty
$$P(x; \mu) = f(x) + \frac{\mu}{2} \max(0, g(x))^2, \quad \mu \to \infty$$
The penalty method approaches the constrained boundary $g(x) = 0$ from the **infeasible exterior** as multiplier $\mu$ increases.

### Logarithmic Interior Barrier
$$B(x; \mu) = f(x) - \mu \ln(-g(x)), \quad \mu \to 0^+$$
The barrier method creates an infinite potential singularity at the constraint boundary, ensuring all iterates remain **strictly feasible (interior)**.

::: barrier-vs-penalty
:::

---

## 4. Algorithmic Decision Architecture

Select the optimal solver family based on convexity, dimension, gradient availability, and constraint structure:

::: decision-ladder
:::
