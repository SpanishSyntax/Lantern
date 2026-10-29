/**
 * Lantern Barrier vs. Penalty Interactive Constraint Lab Widget
 * Mathematical relaxation methods:
 * Quadratic Penalty: P(x; μ) = f(x) + (μ / 2) [max(0, g(x))]^2,  μ -> ∞
 * Log Barrier:       B(x; μ) = f(x) - μ ln(-g(x)),               μ -> 0^+
 */

(function () {
  'use strict';

  class BarrierLabWidget {
    constructor(container) {
      this.container = container;
      this.canvas2D = container.querySelector('.lantern-barrier-canvas-2d');
      this.ctx2D = this.canvas2D.getContext('2d');

      this.canvas1D = container.querySelector('.lantern-barrier-canvas-1d');
      this.ctx1D = this.canvas1D.getContext('2d');

      this.mode = 'penalty'; // 'penalty' or 'barrier'
      this.mu = 1.0;         // current multiplier

      // Problem definition:
      // min f(x, y) = 0.5 * ((x - 2.5)^2 + (y - 2.5)^2)
      // s.t. g(x, y) = x + y - 2.0 <= 0
      // Unconstrained min: (2.5, 2.5)
      // Constrained min on boundary: (1.0, 1.0)
      this.f = (x, y) => 0.5 * ((x - 2.5) ** 2 + (y - 2.5) ** 2);
      this.g = (x, y) => x + y - 2.0;

      this.domain = [-0.5, 3.5, -0.5, 3.5];

      this.initUI();
      this.resizeCanvases();
      this.render();
    }

    initUI() {
      // Mode selector
      const modeRadios = this.container.querySelectorAll('[data-control="mode"]');
      modeRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
          this.mode = e.target.value;
          this.updateSliderRange();
          this.render();
        });
      });

      // Mu slider
      const slider = this.container.querySelector('[data-control="mu"]');
      const valDisplay = this.container.querySelector('[data-val="mu"]');
      if (slider) {
        slider.addEventListener('input', (e) => {
          const exponent = parseFloat(e.target.value);
          this.mu = Math.pow(10, exponent);
          if (valDisplay) valDisplay.textContent = this.mu < 0.1 ? this.mu.toFixed(3) : this.mu.toFixed(2);
          this.render();
        });
      }

      window.addEventListener('resize', () => {
        this.resizeCanvases();
        this.render();
      });
    }

    updateSliderRange() {
      const slider = this.container.querySelector('[data-control="mu"]');
      const label = this.container.querySelector('[data-label="mu"]');
      if (this.mode === 'penalty') {
        if (label) label.textContent = 'Penalty Multiplier μ (→ ∞)';
      } else {
        if (label) label.textContent = 'Barrier Multiplier μ (→ 0⁺)';
      }
    }

    resizeCanvases() {
      const dpr = window.devicePixelRatio || 1;

      [this.canvas2D, this.canvas1D].forEach(cv => {
        const rect = cv.getBoundingClientRect();
        const w = Math.max(260, Math.floor(rect.width));
        const h = Math.max(240, Math.floor(rect.height || w * 0.85));
        cv.width = w * dpr;
        cv.height = h * dpr;
        const ctx = cv.getContext('2d');
        ctx.resetTransform?.();
        ctx.scale(dpr, dpr);
        cv._dw = w;
        cv._dh = h;
      });
    }

    // Solve for minimizer along the symmetric line x = y
    // For x = y: g(x, x) = 2x - 2. Feasible for x <= 1.0. Unconstrained min at x = 2.5.
    // Penalty: P(x) = (x - 2.5)^2 + 0.5 * mu * max(0, 2x - 2)^2
    // Derivative: 2(x - 2.5) + 2 * mu * (2x - 2) * 2 = 0
    // => (x - 2.5) + 4 mu (x - 1) = 0 => x (1 + 4 mu) = 2.5 + 4 mu => x*(mu) = (2.5 + 4 mu) / (1 + 4 mu)
    // As mu -> 0: x* = 2.5 (unconstrained). As mu -> inf: x* -> 1.0 (approaching from exterior/infeasible!)
    // Barrier: B(x) = (x - 2.5)^2 - mu * ln(2 - 2x) for x < 1.0
    // Derivative: 2(x - 2.5) + mu * 2 / (2 - 2x) = 0 => (x - 2.5) + mu / (1 - x) = 0
    // => (x - 2.5)(1 - x) + mu = 0 => -x^2 + 3.5x - 2.5 + mu = 0 => x^2 - 3.5x + (2.5 - mu) = 0
    // Quadratic formula root in (-inf, 1): x = (3.5 - sqrt(3.5^2 - 4(2.5 - mu))) / 2
    getMinimizer() {
      if (this.mode === 'penalty') {
        const x = (2.5 + 4 * this.mu) / (1 + 4 * this.mu);
        return [x, x];
      } else {
        // Barrier
        const disc = 3.5 * 3.5 - 4 * (2.5 - Math.min(this.mu, 0.5));
        if (disc >= 0) {
          const x = (3.5 - Math.sqrt(disc)) / 2;
          return [x, x];
        }
        return [0.95, 0.95];
      }
    }

    render2D() {
      const ctx = this.ctx2D;
      const w = this.canvas2D._dw;
      const h = this.canvas2D._dh;
      const [xmin, xmax, ymin, ymax] = this.domain;

      const toScreen = (x, y) => [
        ((x - xmin) / (xmax - xmin)) * w,
        ((ymax - y) / (ymax - ymin)) * h
      ];

      ctx.clearRect(0, 0, w, h);

      // 1. Shaded Feasible Region: g(x, y) = x + y - 2 <= 0 => y <= 2 - x
      ctx.fillStyle = 'rgba(52, 211, 153, 0.08)';
      ctx.beginPath();
      const [p1x, p1y] = toScreen(xmin, ymin);
      const [p2x, p2y] = toScreen(xmin, 2 - xmin);
      const [p3x, p3y] = toScreen(2 - ymin, ymin);
      ctx.moveTo(p1x, p1y);
      ctx.lineTo(p2x, p2y);
      ctx.lineTo(p3x, p3y);
      ctx.closePath();
      ctx.fill();

      // Feasible region label
      ctx.fillStyle = 'rgba(52, 211, 153, 0.5)';
      ctx.font = '11px sans-serif';
      ctx.fillText('Feasible Region g(x) ≤ 0', p1x + 15, p1y - 20);

      // 2. Constraint boundary line g(x, y) = 0
      ctx.strokeStyle = '#fbbf24';
      ctx.lineWidth = 2.5;
      ctx.setLineDash([6, 4]);
      ctx.beginPath();
      const [b1x, b1y] = toScreen(-0.5, 2.5);
      const [b2x, b2y] = toScreen(2.5, -0.5);
      ctx.moveTo(b1x, b1y);
      ctx.lineTo(b2x, b2y);
      ctx.stroke();
      ctx.setLineDash([]);

      // 3. Objective contours: concentric circles around (2.5, 2.5)
      const [cx, cy] = toScreen(2.5, 2.5);
      ctx.strokeStyle = 'rgba(56, 189, 248, 0.2)';
      ctx.lineWidth = 1;
      for (let rVal = 0.5; rVal <= 3.5; rVal += 0.5) {
        const radiusPx = (rVal / (xmax - xmin)) * w;
        ctx.beginPath();
        ctx.arc(cx, cy, radiusPx, 0, Math.PI * 2);
        ctx.stroke();
      }

      // 4. Points:
      // Unconstrained minimizer (2.5, 2.5)
      ctx.fillStyle = '#f43f5e';
      ctx.beginPath();
      ctx.arc(cx, cy, 5, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = '#f8fafc';
      ctx.font = '11px sans-serif';
      ctx.fillText('x* unc (2.5, 2.5)', cx + 8, cy - 6);

      // Constrained true minimum (1.0, 1.0)
      const [conX, conY] = toScreen(1.0, 1.0);
      ctx.fillStyle = '#34d399';
      ctx.beginPath();
      ctx.arc(conX, conY, 5, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillText('x* con (1.0, 1.0)', conX - 90, conY + 16);

      // Current minimizer x*(mu)
      const [curX, curY] = this.getMinimizer();
      const [sx, sy] = toScreen(curX, curY);

      // Trace line from unconstrained/interior to current
      ctx.strokeStyle = this.mode === 'penalty' ? 'rgba(251, 191, 36, 0.4)' : 'rgba(167, 139, 250, 0.4)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(conX, conY);
      ctx.lineTo(sx, sy);
      ctx.stroke();

      ctx.fillStyle = this.mode === 'penalty' ? '#fbbf24' : '#a78bfa';
      ctx.beginPath();
      ctx.arc(sx, sy, 7, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Title & Annotation
      ctx.fillStyle = '#94a3b8';
      ctx.font = '11px sans-serif';
      ctx.fillText('2D Parameter Space (x, y)', 12, 20);
    }

    render1D() {
      const ctx = this.ctx1D;
      const w = this.canvas1D._dw;
      const h = this.canvas1D._dh;

      ctx.clearRect(0, 0, w, h);

      // Cross-section slice along line x = y from s = 0.0 to s = 3.0
      // Boundary is at s = 1.0. Feasible: s <= 1.0.
      const sMin = 0.0, sMax = 2.8;
      const toScreen = (s, val) => [
        ((s - sMin) / (sMax - sMin)) * (w - 40) + 25,
        h - 25 - (Math.min(val, 6.0) / 6.0) * (h - 50)
      ];

      // Draw axis
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
      ctx.lineWidth = 1;
      const [ax0X, ax0Y] = toScreen(sMin, 0);
      const [ax1X, ax1Y] = toScreen(sMax, 0);
      ctx.beginPath();
      ctx.moveTo(ax0X, ax0Y);
      ctx.lineTo(ax1X, ax1Y);
      ctx.stroke();

      // Boundary vertical line at s = 1.0
      const [bx0, by0] = toScreen(1.0, 0);
      const [bx1, by1] = toScreen(1.0, 6.0);
      ctx.strokeStyle = '#fbbf24';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(bx0, by0);
      ctx.lineTo(bx1, by1);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.fillStyle = '#fbbf24';
      ctx.font = '10px sans-serif';
      ctx.fillText('Boundary s=1.0', bx0 + 4, 30);

      // Objective f(s) curve (unpenalized)
      ctx.strokeStyle = 'rgba(56, 189, 248, 0.4)';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      for (let s = sMin; s <= sMax; s += 0.05) {
        const val = (s - 2.5) ** 2;
        const [px, py] = toScreen(s, val);
        if (s === sMin) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.stroke();

      // Combined augmented objective curve
      const color = this.mode === 'penalty' ? '#fbbf24' : '#a78bfa';
      ctx.strokeStyle = color;
      ctx.lineWidth = 2.5;
      ctx.beginPath();

      let started = false;
      for (let s = sMin; s <= sMax; s += 0.02) {
        let val;
        if (this.mode === 'penalty') {
          const viol = Math.max(0, 2 * s - 2);
          val = (s - 2.5) ** 2 + 0.5 * this.mu * (viol ** 2);
        } else {
          // Barrier
          if (s >= 0.999) continue;
          val = (s - 2.5) ** 2 - this.mu * Math.log(Math.max(1e-5, 2 - 2 * s));
        }

        if (isNaN(val) || val > 6.0) {
          started = false;
          continue;
        }

        const [px, py] = toScreen(s, val);
        if (!started) {
          ctx.moveTo(px, py);
          started = true;
        } else {
          ctx.lineTo(px, py);
        }
      }
      ctx.stroke();

      // Minimizer marker on 1D curve
      const [curX] = this.getMinimizer();
      let curVal;
      if (this.mode === 'penalty') {
        const viol = Math.max(0, 2 * curX - 2);
        curVal = (curX - 2.5) ** 2 + 0.5 * this.mu * (viol ** 2);
      } else {
        curVal = (curX - 2.5) ** 2 - this.mu * Math.log(Math.max(1e-5, 2 - 2 * curX));
      }

      const [mX, mY] = toScreen(curX, curVal);
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(mX, mY, 6, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1.5;
      ctx.stroke();

      ctx.fillStyle = '#94a3b8';
      ctx.font = '11px sans-serif';
      ctx.fillText('1D Slice: Augmented Objective vs Constraint Wall', 12, 20);
    }

    render() {
      this.render2D();
      this.render1D();
      this.updateMetrics();
    }

    updateMetrics() {
      const [x, y] = this.getMinimizer();
      const fVal = this.f(x, y);
      const gVal = this.g(x, y);
      const viol = Math.max(0, gVal);

      const setVal = (key, txt) => {
        const el = this.container.querySelector(`[data-metric="${key}"]`);
        if (el) el.textContent = txt;
      };

      setVal('mu', this.mu < 0.1 ? this.mu.toFixed(3) : this.mu.toFixed(2));
      setVal('pos', `(${x.toFixed(3)}, ${y.toFixed(3)})`);
      setVal('f', fVal.toFixed(4));
      setVal('viol', viol < 1e-4 ? '0.000 (Feasible)' : viol.toFixed(3));
      setVal('status', viol < 1e-4 ? 'Feasible (Interior)' : 'Infeasible (Exterior Penalty)');
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.lantern-barrier-container').forEach(el => {
      new BarrierLabWidget(el);
    });
  });
})();
