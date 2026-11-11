/**
 * Lantern Canvas Walker - Real-time Optimization Trajectory Simulation Widget
 * Supports: Rosenbrock, Ill-Conditioned Ellipse, Rastrigin, Saddle
 * Algorithms: Gradient Descent (GD), Armijo Backtracking, Newton-Raphson, BFGS, Momentum
 */

(function () {
  'use strict';

  // Landscapes definition: f(x, y), grad(x, y), hess(x, y), domain [xmin, xmax, ymin, ymax]
  const LANDSCAPES = {
    rosenbrock: {
      name: "Rosenbrock Banana Valley",
      domain: [-2.0, 2.0, -1.0, 3.0],
      defaultSeed: [-1.2, 1.0],
      f: (x, y) => (1 - x) ** 2 + 100 * (y - x * x) ** 2,
      grad: (x, y) => [
        -2 * (1 - x) - 400 * x * (y - x * x),
        200 * (y - x * x)
      ],
      hess: (x, y) => [
        [2 - 400 * (y - 3 * x * x), -400 * x],
        [-400 * x, 200]
      ],
      min: [1.0, 1.0]
    },
    ellipse: {
      name: "Ill-Conditioned Elliptic Bowl (κ = 20)",
      domain: [-4.0, 4.0, -4.0, 4.0],
      defaultSeed: [-3.0, 2.5],
      f: (x, y) => 0.5 * (x * x + 20 * y * y),
      grad: (x, y) => [x, 20 * y],
      hess: (x, y) => [
        [1.0, 0.0],
        [0.0, 20.0]
      ],
      min: [0.0, 0.0]
    },
    rastrigin: {
      name: "Rastrigin Multimodal Surface",
      domain: [-3.0, 3.0, -3.0, 3.0],
      defaultSeed: [-2.2, 2.4],
      f: (x, y) => 20 + (x * x - 10 * Math.cos(2 * Math.PI * x)) + (y * y - 10 * Math.cos(2 * Math.PI * y)),
      grad: (x, y) => [
        2 * x + 20 * Math.PI * Math.sin(2 * Math.PI * x),
        2 * y + 20 * Math.PI * Math.sin(2 * Math.PI * y)
      ],
      hess: (x, y) => [
        [2 + 40 * Math.PI * Math.PI * Math.cos(2 * Math.PI * x), 0],
        [0, 2 + 40 * Math.PI * Math.PI * Math.cos(2 * Math.PI * y)]
      ],
      min: [0.0, 0.0]
    },
    saddle: {
      name: "Hyperbolic Saddle Point",
      domain: [-3.0, 3.0, -3.0, 3.0],
      defaultSeed: [-0.05, 2.5],
      f: (x, y) => x * x - y * y,
      grad: (x, y) => [2 * x, -2 * y],
      hess: (x, y) => [
        [2.0, 0.0],
        [0.0, -2.0]
      ],
      min: [0.0, 0.0]
    }
  };

  const ALGO_COLORS = {
    gd: '#38bdf8',       // Cyan
    armijo: '#a78bfa',   // Purple
    newton: '#34d399',   // Emerald
    bfgs: '#fbbf24',     // Amber
    momentum: '#f43f5e'  // Rose
  };

  const ALGO_NAMES = {
    gd: 'Gradient Descent',
    armijo: 'GD + Armijo Backtrack',
    newton: 'Newton-Raphson',
    bfgs: 'Quasi-Newton BFGS',
    momentum: 'Polyak Momentum'
  };

  class WalkerWidget {
    constructor(container) {
      this.container = container;
      this.landscapeKey = container.getAttribute('data-landscape') || 'rosenbrock';
      if (!LANDSCAPES[this.landscapeKey]) this.landscapeKey = 'rosenbrock';

      const algoAttr = container.getAttribute('data-algorithms') || 'gd,armijo,newton,bfgs,momentum';
      this.enabledAlgos = new Set(algoAttr.split(',').map(s => s.trim().toLowerCase()));

      this.activeAlgos = new Set(this.enabledAlgos);
      this.canvas = container.querySelector('.lantern-walker-canvas');
      this.ctx = this.canvas.getContext('2d');

      this.alpha = 0.002;
      this.beta = 0.85; // momentum parameter
      this.maxSteps = 60;
      this.currentStep = 0;
      this.animating = false;
      this.animTimer = null;

      const ls = LANDSCAPES[this.landscapeKey];
      this.seed = [...ls.defaultSeed];
      this.trajectories = {};

      this.bgOffscreen = document.createElement('canvas');
      this.bgCtx = this.bgOffscreen.getContext('2d');
      this.bgDirty = true;

      this.initUI();
      this.bindEvents();
      this.resizeCanvas();
      this.computeTrajectories();
      this.render();
    }

    initUI() {
      // Landscape selector
      const lsSelect = this.container.querySelector('[data-control="landscape"]');
      if (lsSelect) {
        lsSelect.value = this.landscapeKey;
        lsSelect.addEventListener('change', (e) => {
          this.landscapeKey = e.target.value;
          this.seed = [...LANDSCAPES[this.landscapeKey].defaultSeed];
          this.bgDirty = true;
          this.currentStep = this.maxSteps;
          this.computeTrajectories();
          this.render();
        });
      }

      // Algorithm tags
      const tagContainer = this.container.querySelector('.lantern-algo-tags');
      if (tagContainer) {
        tagContainer.innerHTML = '';
        for (const [key, name] of Object.entries(ALGO_NAMES)) {
          if (!this.enabledAlgos.has(key)) continue;
          const tag = document.createElement('div');
          tag.className = 'lantern-algo-tag' + (this.activeAlgos.has(key) ? ' active' : '');
          tag.dataset.algo = key;
          tag.innerHTML = `
            <span class="lantern-algo-dot" style="background: ${ALGO_COLORS[key]}"></span>
            <span>${name}</span>
          `;
          tag.addEventListener('click', () => {
            if (this.activeAlgos.has(key)) {
              if (this.activeAlgos.size > 1) this.activeAlgos.delete(key);
            } else {
              this.activeAlgos.add(key);
            }
            tag.classList.toggle('active', this.activeAlgos.has(key));
            this.render();
          });
          tagContainer.appendChild(tag);
        }
      }

      // Slider: Alpha
      const alphaSlider = this.container.querySelector('[data-control="alpha"]');
      const alphaVal = this.container.querySelector('[data-val="alpha"]');
      if (alphaSlider) {
        if (this.landscapeKey === 'rosenbrock') this.alpha = 0.0015;
        else if (this.landscapeKey === 'ellipse') this.alpha = 0.05;
        alphaSlider.value = this.alpha;
        if (alphaVal) alphaVal.textContent = Number(this.alpha).toFixed(4);

        alphaSlider.addEventListener('input', (e) => {
          this.alpha = parseFloat(e.target.value);
          if (alphaVal) alphaVal.textContent = Number(this.alpha).toFixed(4);
          this.computeTrajectories();
          this.render();
        });
      }

      // Slider: Momentum Beta
      const betaSlider = this.container.querySelector('[data-control="beta"]');
      const betaVal = this.container.querySelector('[data-val="beta"]');
      if (betaSlider) {
        betaSlider.value = this.beta;
        if (betaVal) betaVal.textContent = Number(this.beta).toFixed(2);
        betaSlider.addEventListener('input', (e) => {
          this.beta = parseFloat(e.target.value);
          if (betaVal) betaVal.textContent = Number(this.beta).toFixed(2);
          this.computeTrajectories();
          this.render();
        });
      }

      // Step slider
      const stepSlider = this.container.querySelector('[data-control="steps"]');
      const stepVal = this.container.querySelector('[data-val="steps"]');
      if (stepSlider) {
        stepSlider.value = this.maxSteps;
        this.currentStep = this.maxSteps;
        if (stepVal) stepVal.textContent = this.maxSteps;
        stepSlider.addEventListener('input', (e) => {
          this.maxSteps = parseInt(e.target.value, 10);
          this.currentStep = this.maxSteps;
          if (stepVal) stepVal.textContent = this.maxSteps;
          this.computeTrajectories();
          this.render();
        });
      }

      // Buttons
      const playBtn = this.container.querySelector('[data-action="play"]');
      if (playBtn) {
        playBtn.addEventListener('click', () => {
          if (this.currentStep < this.maxSteps) {
            this.currentStep++;
          } else {
            this.currentStep = 1;
          }
          this.render();
        });
      }

      const animateBtn = this.container.querySelector('[data-action="animate"]');
      if (animateBtn) {
        animateBtn.addEventListener('click', () => {
          this.toggleAnimate(animateBtn);
        });
      }

      const resetBtn = this.container.querySelector('[data-action="reset"]');
      if (resetBtn) {
        resetBtn.addEventListener('click', () => {
          this.stopAnimate();
          this.currentStep = this.maxSteps;
          this.seed = [...LANDSCAPES[this.landscapeKey].defaultSeed];
          this.computeTrajectories();
          this.render();
        });
      }
    }

    toggleAnimate(btn) {
      if (this.animating) {
        this.stopAnimate();
        if (btn) btn.textContent = 'Animate';
      } else {
        this.animating = true;
        this.currentStep = 0;
        if (btn) btn.textContent = 'Pause';
        this.animTimer = setInterval(() => {
          if (this.currentStep < this.maxSteps) {
            this.currentStep++;
            this.render();
          } else {
            this.stopAnimate();
            if (btn) btn.textContent = 'Animate';
          }
        }, 60);
      }
    }

    stopAnimate() {
      this.animating = false;
      if (this.animTimer) clearInterval(this.animTimer);
      this.animTimer = null;
    }

    bindEvents() {
      let isDragging = false;
      const getCoord = (e) => {
        const rect = this.canvas.getBoundingClientRect();
        const px = e.clientX - rect.left;
        const py = e.clientY - rect.top;
        const [xmin, xmax, ymin, ymax] = LANDSCAPES[this.landscapeKey].domain;
        const x = xmin + (px / rect.width) * (xmax - xmin);
        const y = ymax - (py / rect.height) * (ymax - ymin);
        return [x, y];
      };

      this.canvas.addEventListener('mousedown', (e) => {
        isDragging = true;
        this.seed = getCoord(e);
        this.computeTrajectories();
        this.render();
      });

      window.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        this.seed = getCoord(e);
        this.computeTrajectories();
        this.render();
      });

      window.addEventListener('mouseup', () => {
        isDragging = false;
      });

      window.addEventListener('resize', () => {
        this.resizeCanvas();
        this.bgDirty = true;
        this.render();
      });
    }

    resizeCanvas() {
      const dpr = window.devicePixelRatio || 1;
      const rect = this.canvas.getBoundingClientRect();
      const w = Math.max(280, Math.floor(rect.width));
      const h = Math.max(280, Math.floor(rect.height || w));

      this.canvas.width = w * dpr;
      this.canvas.height = h * dpr;
      this.ctx.resetTransform?.();
      this.ctx.scale(dpr, dpr);

      this.bgOffscreen.width = w;
      this.bgOffscreen.height = h;
      this.displayW = w;
      this.displayH = h;
    }

    toScreen(x, y) {
      const [xmin, xmax, ymin, ymax] = LANDSCAPES[this.landscapeKey].domain;
      const sx = ((x - xmin) / (xmax - xmin)) * this.displayW;
      const sy = ((ymax - y) / (ymax - ymin)) * this.displayH;
      return [sx, sy];
    }

    computeTrajectories() {
      const ls = LANDSCAPES[this.landscapeKey];
      this.trajectories = {};

      for (const algo of this.enabledAlgos) {
        const path = [];
        let curr = [...this.seed];
        path.push({ x: curr[0], y: curr[1], f: ls.f(curr[0], curr[1]), gradNorm: Math.hypot(...ls.grad(curr[0], curr[1])) });

        let vel = [0, 0];
        let B = [[1, 0], [0, 1]]; // Inverse Hessian approx for BFGS

        for (let k = 0; k < this.maxSteps; k++) {
          const [gx, gy] = ls.grad(curr[0], curr[1]);
          const gNorm = Math.hypot(gx, gy);
          if (isNaN(curr[0]) || isNaN(curr[1]) || gNorm < 1e-6 || Math.abs(curr[0]) > 20 || Math.abs(curr[1]) > 20) break;

          let stepX = 0, stepY = 0;

          if (algo === 'gd') {
            stepX = -this.alpha * gx;
            stepY = -this.alpha * gy;
          } else if (algo === 'momentum') {
            vel[0] = this.beta * vel[0] - this.alpha * gx;
            vel[1] = this.beta * vel[1] - this.alpha * gy;
            stepX = vel[0];
            stepY = vel[1];
          } else if (algo === 'armijo') {
            let armijoAlpha = Math.max(this.alpha * 5, 0.02);
            const c = 1e-4;
            const rho = 0.5;
            const f0 = ls.f(curr[0], curr[1]);
            for (let i = 0; i < 15; i++) {
              const candX = curr[0] - armijoAlpha * gx;
              const candY = curr[1] - armijoAlpha * gy;
              if (ls.f(candX, candY) <= f0 - c * armijoAlpha * (gNorm * gNorm)) {
                break;
              }
              armijoAlpha *= rho;
            }
            stepX = -armijoAlpha * gx;
            stepY = -armijoAlpha * gy;
          } else if (algo === 'newton') {
            const [[h11, h12], [h21, h22]] = ls.hess(curr[0], curr[1]);
            // Regularize Hessian: H + λI
            const lambda = 1e-3;
            const a = h11 + lambda, b = h12, c = h21, d = h22 + lambda;
            const det = a * d - b * c;
            if (Math.abs(det) > 1e-9) {
              const inv11 = d / det, inv12 = -b / det;
              const inv21 = -c / det, inv22 = a / det;
              stepX = -(inv11 * gx + inv12 * gy);
              stepY = -(inv21 * gx + inv22 * gy);
              // Line search / clamp step length for stability
              const sNorm = Math.hypot(stepX, stepY);
              if (sNorm > 1.5) {
                stepX = (stepX / sNorm) * 1.5;
                stepY = (stepY / sNorm) * 1.5;
              }
            } else {
              stepX = -this.alpha * gx;
              stepY = -this.alpha * gy;
            }
          } else if (algo === 'bfgs') {
            // d = - B * g
            const dx = -(B[0][0] * gx + B[0][1] * gy);
            const dy = -(B[1][0] * gx + B[1][1] * gy);
            // Armijo on BFGS direction
            let lr = 1.0;
            const f0 = ls.f(curr[0], curr[1]);
            const dirDotGrad = dx * gx + dy * gy;
            if (dirDotGrad < 0) {
              for (let i = 0; i < 10; i++) {
                const cx = curr[0] + lr * dx;
                const cy = curr[1] + lr * dy;
                if (ls.f(cx, cy) <= f0 + 1e-4 * lr * dirDotGrad) break;
                lr *= 0.5;
              }
            } else {
              lr = this.alpha;
            }
            stepX = lr * dx;
            stepY = lr * dy;

            const nextX = curr[0] + stepX;
            const nextY = curr[1] + stepY;
            const [nextGx, nextGy] = ls.grad(nextX, nextY);
            const s = [stepX, stepY];
            const y = [nextGx - gx, nextGy - gy];
            const sy = s[0] * y[0] + s[1] * y[1];
            if (sy > 1e-8) {
              const rho = 1.0 / sy;
              // B = (I - rho*s*y^T) B (I - rho*y*s^T) + rho*s*s^T
              const syt00 = 1 - rho * s[0] * y[0], syt01 = -rho * s[0] * y[1];
              const syt10 = -rho * s[1] * y[0], syt11 = 1 - rho * s[1] * y[1];

              const yst00 = 1 - rho * y[0] * s[0], yst01 = -rho * y[0] * s[1];
              const yst10 = -rho * y[1] * s[0], yst11 = 1 - rho * y[1] * s[1];

              // M = syt * B
              const m00 = syt00 * B[0][0] + syt01 * B[1][0];
              const m01 = syt00 * B[0][1] + syt01 * B[1][1];
              const m10 = syt10 * B[0][0] + syt11 * B[1][0];
              const m11 = syt10 * B[0][1] + syt11 * B[1][1];

              // N = M * yst
              const n00 = m00 * yst00 + m01 * yst10;
              const n01 = m00 * yst01 + m01 * yst11;
              const n10 = m10 * yst00 + m11 * yst10;
              const n11 = m10 * yst01 + m11 * yst11;

              B[0][0] = n00 + rho * s[0] * s[0];
              B[0][1] = n01 + rho * s[0] * s[1];
              B[1][0] = n10 + rho * s[1] * s[0];
              B[1][1] = n11 + rho * s[1] * s[1];
            }
          }

          curr = [curr[0] + stepX, curr[1] + stepY];
          path.push({
            x: curr[0],
            y: curr[1],
            f: ls.f(curr[0], curr[1]),
            gradNorm: Math.hypot(...ls.grad(curr[0], curr[1]))
          });
        }
        this.trajectories[algo] = path;
      }
    }

    renderBackground() {
      if (!this.bgDirty) return;
      const w = this.bgOffscreen.width;
      const h = this.bgOffscreen.height;
      const ctx = this.bgCtx;
      const ls = LANDSCAPES[this.landscapeKey];
      const [xmin, xmax, ymin, ymax] = ls.domain;

      const imgData = ctx.createImageData(w, h);
      const data = imgData.data;

      // Sample resolution for performance
      const step = 2;
      for (let py = 0; py < h; py += step) {
        const y = ymax - (py / h) * (ymax - ymin);
        for (let px = 0; px < w; px += step) {
          const x = xmin + (px / w) * (xmax - xmin);
          const val = ls.f(x, y);

          // Logarithmic elevation normalization
          let norm = Math.log10(Math.max(1e-4, val + 1)) / 4.0;
          norm = Math.min(1.0, Math.max(0.0, norm));

          // Frost dark heatmap: deep navy -> indigo -> teal -> electric cyan
          const r = Math.floor(10 + norm * 20);
          const g = Math.floor(16 + norm * 50);
          const b = Math.floor(32 + norm * 100);

          // Contour lines effect
          const isoline = Math.abs(Math.sin(norm * 35));
          const isIso = isoline < 0.12 ? 30 : 0;

          for (let dy = 0; dy < step && py + dy < h; dy++) {
            for (let dx = 0; dx < step && px + dx < w; dx++) {
              const idx = ((py + dy) * w + (px + dx)) * 4;
              data[idx] = Math.min(255, r + isIso);
              data[idx + 1] = Math.min(255, g + isIso);
              data[idx + 2] = Math.min(255, b + isIso);
              data[idx + 3] = 255;
            }
          }
        }
      }
      ctx.putImageData(imgData, 0, 0);

      // Coordinate axes
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
      ctx.lineWidth = 1;
      const [axX, axY] = this.toScreen(0, 0);
      ctx.beginPath();
      ctx.moveTo(0, axY);
      ctx.lineTo(w, axY);
      ctx.moveTo(axX, 0);
      ctx.lineTo(axX, h);
      ctx.stroke();

      // Optimum marker
      const [optX, optY] = this.toScreen(ls.min[0], ls.min[1]);
      ctx.fillStyle = '#34d399';
      ctx.beginPath();
      ctx.arc(optX, optY, 4, 0, Math.PI * 2);
      ctx.fill();

      this.bgDirty = false;
    }

    render() {
      this.renderBackground();
      this.ctx.clearRect(0, 0, this.displayW, this.displayH);
      this.ctx.drawImage(this.bgOffscreen, 0, 0, this.displayW, this.displayH);

      // Render trajectories
      const stepLimit = Math.min(this.maxSteps, this.currentStep);

      for (const algo of this.activeAlgos) {
        const path = this.trajectories[algo];
        if (!path || path.length === 0) continue;

        const color = ALGO_COLORS[algo] || '#ffffff';
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = 2.5;
        this.ctx.beginPath();

        const [s0X, s0Y] = this.toScreen(path[0].x, path[0].y);
        this.ctx.moveTo(s0X, s0Y);

        const n = Math.min(path.length, stepLimit + 1);
        for (let i = 1; i < n; i++) {
          const [sx, sy] = this.toScreen(path[i].x, path[i].y);
          this.ctx.lineTo(sx, sy);
        }
        this.ctx.stroke();

        // Points
        for (let i = 0; i < n; i++) {
          const [sx, sy] = this.toScreen(path[i].x, path[i].y);
          this.ctx.fillStyle = i === n - 1 ? '#ffffff' : color;
          this.ctx.beginPath();
          this.ctx.arc(sx, sy, i === n - 1 ? 5 : 2.5, 0, Math.PI * 2);
          this.ctx.fill();
        }
      }

      // Seed marker
      const [seedX, seedY] = this.toScreen(this.seed[0], this.seed[1]);
      this.ctx.fillStyle = '#f8fafc';
      this.ctx.strokeStyle = '#38bdf8';
      this.ctx.lineWidth = 2;
      this.ctx.beginPath();
      this.ctx.arc(seedX, seedY, 6, 0, Math.PI * 2);
      this.ctx.fill();
      this.ctx.stroke();

      this.updateMetrics();
    }

    updateMetrics() {
      // Pick first active algorithm for readout
      const firstAlgo = [...this.activeAlgos][0] || 'gd';
      const path = this.trajectories[firstAlgo];
      if (!path) return;

      const idx = Math.min(path.length - 1, this.currentStep);
      const pt = path[idx];

      const setVal = (key, txt) => {
        const el = this.container.querySelector(`[data-metric="${key}"]`);
        if (el) el.textContent = txt;
      };

      setVal('iter', `${idx} / ${this.maxSteps}`);
      setVal('coord', `(${pt.x.toFixed(3)}, ${pt.y.toFixed(3)})`);
      setVal('fval', pt.f < 1e-4 ? pt.f.toExponential(3) : pt.f.toFixed(4));
      setVal('grad', pt.gradNorm < 1e-4 ? pt.gradNorm.toExponential(3) : pt.gradNorm.toFixed(4));
    }
  }

  // Auto-discover and initialize all .lantern-walker-container elements
  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.lantern-walker-container').forEach(el => {
      new WalkerWidget(el);
    });
  });
})();
