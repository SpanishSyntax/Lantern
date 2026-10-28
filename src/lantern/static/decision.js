/**
 * Lantern Decision Ladder Wizard Widget
 * Step-by-step interactive decision flowchart for algorithmic and architectural selection
 */

(function () {
  'use strict';

  const DEFAULT_TREE = {
    start: 'convexity',
    nodes: {
      convexity: {
        step: 1,
        question: "Is the objective function convex or non-convex?",
        options: [
          { text: "Strictly Convex / Quadratic", next: "convex_derivatives" },
          { text: "Non-Convex Smooth", next: "nonconvex_derivatives" },
          { text: "Non-Smooth or Discontinuous", next: "nonsmooth_approach" },
          { text: "Black-Box / Simulation / No Formulas", next: "blackbox_approach" }
        ]
      },
      convex_derivatives: {
        step: 2,
        question: "Are analytical first and second-order derivatives available?",
        options: [
          { text: "Exact Hessian & Gradient Accessible", next: "convex_constraints_newton" },
          { text: "Only Gradient (First-order) Accessible", next: "convex_constraints_quasi" },
          { text: "No Derivatives Available (Derivative-Free)", next: "rec_nelder_mead" }
        ]
      },
      convex_constraints_newton: {
        step: 3,
        question: "Are there constraints on parameters?",
        options: [
          { text: "Unconstrained", next: "rec_newton_exact" },
          { text: "Linear Equality / Bound Constraints", next: "rec_newton_kkt" },
          { text: "Nonlinear Inequality Constraints", next: "rec_interior_point" }
        ]
      },
      convex_constraints_quasi: {
        step: 3,
        question: "What is the problem dimension (number of variables $N$)?",
        options: [
          { text: "Small to Medium ($N < 1000$)", next: "rec_bfgs" },
          { text: "Large-Scale ($N > 10^4$)", next: "rec_lbfgs" }
        ]
      },
      nonconvex_derivatives: {
        step: 2,
        question: "What is the training/optimization regime?",
        options: [
          { text: "Deterministic / Batch Optimization", next: "rec_lbfgs_nonconvex" },
          { text: "Stochastic / Deep Learning Minibatches", next: "rec_adam_w" }
        ]
      },
      nonsmooth_approach: {
        step: 2,
        question: "Is the non-smooth term separable (e.g. $L_1$ lasso regularizer)?",
        options: [
          { text: "Yes, Proximal Composite $f(x) + g(x)$", next: "rec_fista" },
          { text: "No, General Subgradient Form", next: "rec_subgradient" }
        ]
      },
      blackbox_approach: {
        step: 2,
        question: "Are evaluations computationally expensive (e.g. physical simulation / CFD)?",
        options: [
          { text: "Expensive ($>1$ sec per eval)", next: "rec_bayesian" },
          { text: "Fast ($<10$ ms per eval)", next: "rec_cmaes" }
        ]
      },
      // Recommendations:
      rec_newton_exact: {
        isResult: true,
        title: "Exact Newton-Raphson with Line Search",
        badge: "Quadratic Convergence",
        badgeColor: "emerald",
        summary: "For unconstrained smooth convex problems with tractable Hessians, Newton-Raphson achieves second-order quadratic local convergence $||x_{k+1} - x^*|| \\le M ||x_k - x^*||^2$ in minimal iterations.",
        pros: ["Superfast quadratic convergence", "Affine invariant"],
        cons: ["Requires computing and inverting $O(N^2)$ Hessian matrix at each step"]
      },
      rec_newton_kkt: {
        isResult: true,
        title: "Equality-Constrained Newton / KKT Solver",
        badge: "Primal-Dual Quadratic",
        badgeColor: "emerald",
        summary: "Solves the Karush-Kuhn-Tucker (KKT) optimality system simultaneously for primal coordinates and Lagrange multipliers.",
        pros: ["Exact satisfaction of linear constraints", "Extremely reliable"],
        cons: ["Indefinite KKT matrix factorization required"]
      },
      rec_interior_point: {
        isResult: true,
        title: "Primal-Dual Interior-Point Method (Barrier)",
        badge: "Industry Standard for NLP",
        badgeColor: "cyan",
        summary: "Transforms inequality constraints $g_i(x) \\le 0$ into logarithmic barriers $-\\mu \\ln(-g_i(x))$ and traces the central path as $\\mu \\to 0$.",
        pros: ["Handles complex nonlinear constraints", "Polynomial time complexity"],
        cons: ["Requires strictly feasible interior initial starting point"]
      },
      rec_bfgs: {
        isResult: true,
        title: "Full BFGS Quasi-Newton",
        badge: "Superlinear Convergence",
        badgeColor: "cyan",
        summary: "Maintains a dense rank-2 symmetric positive-definite approximation $B_k \\approx H^{-1}$ without computing second derivatives.",
        pros: ["Superlinear convergence", "No analytical Hessian needed"],
        cons: ["$O(N^2)$ memory storage for inverse Hessian approximation matrix"]
      },
      rec_lbfgs: {
        isResult: true,
        title: "Limited-Memory BFGS (L-BFGS-B)",
        badge: "High-Dimensional Standard",
        badgeColor: "purple",
        summary: "Stores only the last $m$ curvature vector pairs $(s_k, y_k)$ (typically $m=10$), achieving quasi-Newton speed with $O(mN)$ linear memory.",
        pros: ["Scales gracefully to millions of parameters", "Supports bound box constraints"],
        cons: ["Slightly slower than full Newton on ill-conditioned valleys"]
      },
      rec_lbfgs_nonconvex: {
        isResult: true,
        title: "Damped L-BFGS with Armijo Line Search",
        badge: "Smooth Non-Convex",
        badgeColor: "amber",
        summary: "Utilizes Powell damping or curvature skipping when $s_k^T y_k \\le 0$ to prevent loss of positive-definiteness on non-convex terrain.",
        pros: ["Escapes saddle points when equipped with negative curvature detection"],
        cons: ["Can get trapped in local minima without random restarts"]
      },
      rec_adam_w: {
        isResult: true,
        title: "AdamW (Decoupled Weight Decay Adam)",
        badge: "Stochastic Deep Learning",
        badgeColor: "rose",
        summary: "Maintains running exponential moving averages of both gradients $m_t$ and uncentered variances $v_t$ with decoupled $L_2$ weight decay regularization.",
        pros: ["Robust to noisy mini-batch stochastic gradients", "Adaptive per-coordinate step sizes"],
        cons: ["Hyperparameter sensitivity (learning rate schedule, $\\beta_1, \\beta_2$)"]
      },
      rec_fista: {
        isResult: true,
        title: "FISTA (Fast Iterative Shrinkage-Thresholding)",
        badge: "Accelerated Proximal",
        badgeColor: "cyan",
        summary: "Accelerated proximal gradient method incorporating Nesterov momentum, achieving optimal $O(1/k^2)$ convergence rate for composite problems $f(x) + \\lambda ||x||_1$.",
        pros: ["Exact sparse feature selection via soft-thresholding", "Optimal first-order convergence"],
        cons: ["Requires closed-form proximal operator $\\text{prox}_{\\gamma g}(x)$"]
      },
      rec_subgradient: {
        isResult: true,
        title: "Projected Subgradient Method",
        badge: "Subgradient Calculus",
        badgeColor: "amber",
        summary: "Steps along arbitrary subgradient $g_k \\in \\partial f(x_k)$ with diminishing step size $\\alpha_k = O(1/\\sqrt{k})$.",
        pros: ["Handles non-differentiable convex objectives"],
        cons: ["Slow $O(1/\\sqrt{k})$ convergence rate, no guaranteed descent at each step"]
      },
      rec_nelder_mead: {
        isResult: true,
        title: "Nelder-Mead Downhill Simplex",
        badge: "Zero Derivatives",
        badgeColor: "purple",
        summary: "Maintains a simplex of $N+1$ test points, performing reflections, expansions, and contractions based solely on function evaluations.",
        pros: ["Zero gradient or Jacobian required", "Simple geometric heuristic"],
        cons: ["Degrades rapidly for $N > 15$, can degenerate on elongated valleys"]
      },
      rec_bayesian: {
        isResult: true,
        title: "Bayesian Optimization (Gaussian Processes)",
        badge: "Expensive Black-Box",
        badgeColor: "emerald",
        summary: "Fits a Gaussian Process surrogate model and maximizes an acquisition function (Expected Improvement, Upper Confidence Bound) to choose optimal next sample coordinates.",
        pros: ["Maximizes information gain with minimal function calls", "Uncertainty quantification"],
        cons: ["Surrogate fitting scales as $O(K^3)$ with number of evaluated points"]
      },
      rec_cmaes: {
        isResult: true,
        title: "CMA-ES (Covariance Matrix Adaptation Evolution Strategy)",
        badge: "Evolutionary Black-Box",
        badgeColor: "purple",
        summary: "Adapts a multivariate Gaussian mutation distribution to learn the local second-order covariance metric of the objective landscape.",
        pros: ["Handles rugged, discontinuous, and multimodal landscapes", "Invariance to monotonic transforms"],
        cons: ["Requires thousands to tens of thousands of function evaluations"]
      }
    }
  };

  class DecisionWizard {
    constructor(container) {
      this.container = container;
      this.history = [];
      this.tree = this.loadTree();
      this.currentNodeKey = this.tree.start;

      this.cardContainer = container.querySelector('.lantern-decision-card');
      this.render();
    }

    loadTree() {
      const dataScript = this.container.querySelector('script[type="application/json"]');
      if (dataScript) {
        try {
          const parsed = JSON.parse(dataScript.textContent);
          if (parsed && parsed.nodes) return parsed;
        } catch (e) {
          console.warn('[Lantern] Could not parse decision tree JSON, using built-in optimization tree:', e);
        }
      }
      return DEFAULT_TREE;
    }

    render() {
      const node = this.tree.nodes[this.currentNodeKey];
      if (!node) return;

      this.cardContainer.innerHTML = '';

      if (node.isResult) {
        this.renderResult(node);
      } else {
        this.renderQuestion(node);
      }
    }

    renderQuestion(node) {
      const stepCounter = document.createElement('div');
      stepCounter.className = 'lantern-decision-step-counter';
      stepCounter.textContent = `Step ${this.history.length + 1}`;
      this.cardContainer.appendChild(stepCounter);

      const q = document.createElement('h4');
      q.className = 'lantern-decision-q';
      q.textContent = node.question;
      this.cardContainer.appendChild(q);

      const optGrid = document.createElement('div');
      optGrid.className = 'lantern-decision-options';

      node.options.forEach(opt => {
        const btn = document.createElement('button');
        btn.className = 'lantern-decision-opt-btn';
        btn.innerHTML = `<strong>${opt.text}</strong>`;
        btn.addEventListener('click', () => {
          this.history.push(this.currentNodeKey);
          this.currentNodeKey = opt.next;
          this.render();
        });
        optGrid.appendChild(btn);
      });
      this.cardContainer.appendChild(optGrid);

      if (this.history.length > 0) {
        const backBar = document.createElement('div');
        backBar.style.marginTop = '1.25rem';
        backBar.style.display = 'flex';
        backBar.style.gap = '0.5rem';

        const backBtn = document.createElement('button');
        backBtn.className = 'lantern-btn lantern-btn-sm';
        backBtn.textContent = '← Back';
        backBtn.addEventListener('click', () => {
          this.currentNodeKey = this.history.pop();
          this.render();
        });
        backBar.appendChild(backBtn);
        this.cardContainer.appendChild(backBar);
      }
    }

    renderResult(node) {
      const res = document.createElement('div');
      res.className = 'lantern-decision-result';

      res.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.75rem;">
          <span class="lantern-badge" style="margin-bottom: 0;">Recommended Strategy</span>
          <span class="lantern-badge" style="background: rgba(52, 211, 153, 0.15); color: #34d399; border-color: rgba(52, 211, 153, 0.3); margin-bottom: 0;">${node.badge}</span>
        </div>
        <h3 style="font-size: 1.4rem; color: #ffffff; margin-bottom: 0.75rem;">${node.title}</h3>
        <p style="color: var(--text-secondary); margin-bottom: 1.25rem; font-size: 0.95rem; line-height: 1.6;">${node.summary}</p>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem;">
          <div style="background: var(--bg-deep); padding: 0.85rem; border-radius: 8px; border: 1px solid var(--border-subtle);">
            <strong style="color: #34d399; font-size: 0.85rem;">✓ Advantages</strong>
            <ul style="margin: 0.4rem 0 0 1.2rem; font-size: 0.85rem; color: var(--text-secondary);">
              ${node.pros.map(p => `<li>${p}</li>`).join('')}
            </ul>
          </div>
          <div style="background: var(--bg-deep); padding: 0.85rem; border-radius: 8px; border: 1px solid var(--border-subtle);">
            <strong style="color: #fbbf24; font-size: 0.85rem;">⚠ Tradeoffs / Limits</strong>
            <ul style="margin: 0.4rem 0 0 1.2rem; font-size: 0.85rem; color: var(--text-secondary);">
              ${node.cons.map(c => `<li>${c}</li>`).join('')}
            </ul>
          </div>
        </div>
        <button class="lantern-btn lantern-btn-primary" data-action="restart">Start Over ↺</button>
      `;

      res.querySelector('[data-action="restart"]').addEventListener('click', () => {
        this.history = [];
        this.currentNodeKey = this.tree.start;
        this.render();
      });

      this.cardContainer.appendChild(res);

      if (window.renderMathInElement) {
        window.renderMathInElement(this.cardContainer, { throwOnError: false });
      }
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.lantern-decision-container').forEach(el => {
      new DecisionWizard(el);
    });
  });
})();
