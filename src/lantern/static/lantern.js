/**
 * Lantern Core Client Micro-Runtime
 * High-End Scientific Explainer & Simulation Dashboard Engine
 */

(function () {
  'use strict';

  // Global Lantern namespace
  window.lantern = window.lantern || {};

  // =========================================================================
  // 1. Toast Notification System
  // =========================================================================
  function getOrCreateToastContainer() {
    let container = document.querySelector('.lantern-toast-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'lantern-toast-container';
      document.body.appendChild(container);
    }
    return container;
  }

  window.lantern.toast = function (message, type = 'info') {
    const container = getOrCreateToastContainer();
    const toast = document.createElement('div');
    toast.className = `lantern-toast lantern-toast-${type}`;

    const iconMap = {
      success: '✓',
      error: '✘',
      warning: '⚠',
      info: 'ℹ'
    };
    const icon = iconMap[type] || 'ℹ';

    toast.innerHTML = `<span style="font-weight: bold;">${icon}</span><span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(8px)';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  };

  // =========================================================================
  // 2. Reading Progress Bar
  // =========================================================================
  function initProgressBar() {
    const bar = document.querySelector('.lantern-progress-bar');
    if (!bar) return;

    window.addEventListener('scroll', () => {
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const progress = docHeight > 0 ? (window.scrollY / docHeight) * 100 : 0;
      bar.style.width = `${Math.min(100, Math.max(0, progress))}%`;
    }, { passive: true });
  }

  // =========================================================================
  // 3. Heading Anchors & Permalinks
  // =========================================================================
  function initHeadingAnchors() {
    const headings = document.querySelectorAll('.lantern-prose h1, .lantern-prose h2, .lantern-prose h3, .lantern-prose h4');
    headings.forEach(heading => {
      if (!heading.id) {
        // Auto-generate clean slug
        heading.id = heading.textContent
          .trim()
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, '-')
          .replace(/(^-|-$)/g, '');
      }

      if (heading.querySelector('.lantern-anchor')) return;

      const anchor = document.createElement('a');
      anchor.className = 'lantern-anchor';
      anchor.href = `#${heading.id}`;
      anchor.innerHTML = '#';
      anchor.title = 'Copy link to this section';

      anchor.addEventListener('click', (e) => {
        e.preventDefault();
        const url = `${window.location.origin}${window.location.pathname}#${heading.id}`;
        navigator.clipboard.writeText(url).then(() => {
          history.pushState(null, null, `#${heading.id}`);
          window.lantern.toast('Section link copied to clipboard', 'success');
        });
      });

      heading.prepend(anchor);
    });
  }

  // =========================================================================
  // 3b. Floating Section Dot Navigation Rail (ScrollSpy)
  // =========================================================================
  function initSectionDotNav() {
    const rail = document.getElementById('lantern-dot-nav');
    if (!rail) return;

    // Discover major sections: prefer h2 elements within prose, or h1/h2 if sparse
    let sections = Array.from(document.querySelectorAll('.lantern-prose h2'));
    if (sections.length < 2) {
      sections = Array.from(document.querySelectorAll('.lantern-prose h1, .lantern-prose h2'));
    }

    // Only render dot navigation if there are at least 2 distinct sections
    if (sections.length < 2) {
      rail.style.display = 'none';
      return;
    }

    rail.innerHTML = '';
    const dots = [];

    sections.forEach((heading, index) => {
      if (!heading.id) {
        heading.id = `section-${index + 1}`;
      }

      // Clean title text (strip '#' permalink symbol from textContent)
      const clone = heading.cloneNode(true);
      const permalink = clone.querySelector('.lantern-anchor');
      if (permalink) permalink.remove();
      const titleText = clone.textContent.trim();

      const dot = document.createElement('a');
      dot.className = 'lantern-dot';
      dot.href = `#${heading.id}`;
      dot.setAttribute('aria-label', titleText);
      dot.dataset.target = heading.id;

      const tooltip = document.createElement('span');
      tooltip.className = 'lantern-dot-tooltip';
      tooltip.textContent = titleText;
      dot.appendChild(tooltip);

      dot.addEventListener('click', (e) => {
        e.preventDefault();
        heading.scrollIntoView({ behavior: 'smooth', block: 'start' });
        history.pushState(null, null, `#${heading.id}`);
      });

      rail.appendChild(dot);
      dots.push({ dot, heading });
    });

    // ScrollSpy observer to activate dot corresponding to currently viewed section
    function setActiveDot(activeId) {
      dots.forEach(({ dot }) => {
        const isActive = dot.dataset.target === activeId;
        dot.classList.toggle('active', isActive);
        if (isActive) {
          dot.setAttribute('aria-current', 'true');
        } else {
          dot.removeAttribute('aria-current');
        }
      });
    }

    // Scroll listener fallback & observer for active section detection
    let scrollTimeout;
    function checkActiveByScroll() {
      const scrollPos = window.scrollY + 160;
      let currentId = sections[0].id;
      for (let i = 0; i < sections.length; i++) {
        if (sections[i].offsetTop <= scrollPos) {
          currentId = sections[i].id;
        } else {
          break;
        }
      }
      setActiveDot(currentId);
    }

    window.addEventListener('scroll', () => {
      if (scrollTimeout) cancelAnimationFrame(scrollTimeout);
      scrollTimeout = requestAnimationFrame(checkActiveByScroll);
    }, { passive: true });

    checkActiveByScroll();
  }

  // =========================================================================
  // 4. Lab Atoms & Control Event Dispatch
  // =========================================================================
  function dispatchControlEvent(id, value) {
    window.dispatchEvent(
      new CustomEvent('lantern:input', {
        detail: { id, value },
        bubbles: true
      })
    );
  }

  function initSliders() {
    document.querySelectorAll('.lantern-control-slider').forEach(wrap => {
      const slider = wrap.querySelector('.lantern-slider');
      const valBadge = wrap.querySelector('.lantern-slider-val');
      const id = wrap.dataset.controlId || slider.name || slider.id;
      const unit = slider.dataset.unit || '';

      if (!slider) return;

      slider.addEventListener('input', () => {
        if (valBadge) valBadge.textContent = `${slider.value}${unit}`;
        dispatchControlEvent(id, parseFloat(slider.value));
      });
    });
  }

  function initSwitches() {
    document.querySelectorAll('.lantern-control-switch').forEach(wrap => {
      const cb = wrap.querySelector('input[type="checkbox"]');
      const id = wrap.dataset.controlId || cb.name || cb.id;

      if (!cb) return;

      cb.addEventListener('change', () => {
        dispatchControlEvent(id, cb.checked);
      });
    });
  }

  function initSegments() {
    document.querySelectorAll('.lantern-control-segments').forEach(wrap => {
      const id = wrap.dataset.controlId;
      const hidden = wrap.querySelector('input[type="hidden"]');
      const buttons = wrap.querySelectorAll('.lantern-segment-btn');

      buttons.forEach(btn => {
        btn.addEventListener('click', () => {
          buttons.forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          const val = btn.dataset.val;
          if (hidden) hidden.value = val;
          dispatchControlEvent(id, val);
        });
      });
    });
  }

  function initSelects() {
    document.querySelectorAll('.lantern-control-select').forEach(wrap => {
      const sel = wrap.querySelector('.lantern-select');
      const id = wrap.dataset.controlId || sel.name;

      if (!sel) return;

      sel.addEventListener('change', () => {
        dispatchControlEvent(id, sel.value);
      });
    });
  }

  // =========================================================================
  // 5. Stepper Widget Navigation
  // =========================================================================
  function initSteppers() {
    document.querySelectorAll('.lantern-stepper').forEach(stepper => {
      const navButtons = stepper.querySelectorAll('.lantern-stepper-btn');
      const panes = stepper.querySelectorAll('.lantern-stepper-pane');
      const readout = stepper.querySelector('.lantern-stepper-readout');
      const prevBtn = stepper.querySelector('[data-stepper-action="prev"]');
      const nextBtn = stepper.querySelector('[data-stepper-action="next"]');

      let currentStep = parseInt(stepper.dataset.activeStep || '0', 10);
      const totalSteps = panes.length;

      function updateStep(idx) {
        if (idx < 0) idx = 0;
        if (idx >= totalSteps) idx = totalSteps - 1;
        currentStep = idx;
        stepper.dataset.activeStep = currentStep;

        navButtons.forEach((btn, i) => btn.classList.toggle('active', i === currentStep));
        panes.forEach((pane, i) => pane.classList.toggle('active', i === currentStep));

        if (navButtons[currentStep]) {
          navButtons[currentStep].scrollIntoView({
            behavior: 'smooth',
            block: 'nearest',
            inline: 'nearest'
          });
        }

        if (readout) readout.textContent = `Step ${currentStep + 1} of ${totalSteps}`;
      }

      navButtons.forEach((btn, idx) => {
        btn.addEventListener('click', () => updateStep(idx));
      });

      if (prevBtn) prevBtn.addEventListener('click', () => updateStep(currentStep - 1));
      if (nextBtn) nextBtn.addEventListener('click', () => updateStep(currentStep + 1));
    });
  }

  // =========================================================================
  // 6. Tabs Widget Navigation
  // =========================================================================
  function initTabs() {
    document.querySelectorAll('.lantern-tabs').forEach(tabs => {
      const btns = tabs.querySelectorAll('.lantern-tab-btn');
      const panes = tabs.querySelectorAll('.lantern-tab-pane');

      btns.forEach((btn, idx) => {
        btn.addEventListener('click', () => {
          btns.forEach(b => b.classList.remove('active'));
          panes.forEach(p => p.classList.remove('active'));

          btn.classList.add('active');
          if (panes[idx]) panes[idx].classList.add('active');

          btn.scrollIntoView({
            behavior: 'smooth',
            block: 'nearest',
            inline: 'nearest'
          });
        });
      });
    });
  }

  // =========================================================================
  // 7. Lightbox Modal for Plots
  // =========================================================================
  function getOrCreateLightbox() {
    let overlay = document.querySelector('.lantern-lightbox-overlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.className = 'lantern-lightbox-overlay';
      overlay.innerHTML = `
        <div class="lantern-lightbox-dialog">
          <div class="lantern-lightbox-header">
            <span class="lantern-lightbox-title" style="font-weight: 700; color: #f8fafc;">Plot Lightbox</span>
            <button class="lantern-lightbox-close" aria-label="Close Lightbox">&times;</button>
          </div>
          <div class="lantern-lightbox-content"></div>
        </div>
      `;
      document.body.appendChild(overlay);

      overlay.querySelector('.lantern-lightbox-close').addEventListener('click', () => {
        overlay.classList.remove('active');
      });

      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) overlay.classList.remove('active');
      });

      window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && overlay.classList.contains('active')) {
          overlay.classList.remove('active');
        }
      });
    }
    return overlay;
  }

  function initLightboxes() {
    document.querySelectorAll('.lantern-lightbox-trigger').forEach(btn => {
      btn.addEventListener('click', () => {
        const targetId = btn.dataset.target;
        const wrapper = document.getElementById(targetId);
        if (!wrapper) return;

        const content = wrapper.querySelector('.lantern-plot-content');
        const titleText = wrapper.querySelector('.lantern-plot-title span:last-child')?.textContent || 'Plot Preview';

        const lb = getOrCreateLightbox();
        lb.querySelector('.lantern-lightbox-title').textContent = titleText;
        const lbContent = lb.querySelector('.lantern-lightbox-content');

        lbContent.innerHTML = content ? content.innerHTML : '';
        lb.classList.add('active');
      });
    });
  }

  // =========================================================================
  // 8. KaTeX Math Auto-Render (Scoped & Chunked for Large Documents)
  // =========================================================================
  function initKaTeX() {
    if (typeof renderMathInElement !== 'function') return;

    const katexOptions = {
      delimiters: [
        { left: '$$', right: '$$', display: true },
        { left: '$', right: '$', display: false },
        { left: '\\(', right: '\\)', display: false },
        { left: '\\[', right: '\\]', display: true }
      ],
      throwOnError: false,
      ignoredTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code', 'canvas'],
      ignoredClasses: [
        'plotly',
        'js-plotly-plot',
        'lantern-plot-content',
        'lantern-control-wrap',
        'lantern-slider',
        'lantern-switch',
        'lantern-segment-btn',
        'lantern-stepper-nav',
        'lantern-copy-btn',
        'no-math'
      ]
    };

    // Find scoped content containers to prevent traversing interactive widgets
    const containers = Array.from(document.querySelectorAll(
      '.lantern-prose, .lantern-card-body, .lantern-callout-body, .lantern-tab-panel, .lantern-accordion-body, .lantern-curtain-reveal, .lantern-stepper-content, .lantern-comparison-panel'
    ));

    if (containers.length === 0) {
      // Fallback to main container or body if no specific prose containers match
      const root = document.querySelector('.lantern-container') || document.body;
      try {
        renderMathInElement(root, katexOptions);
      } catch (err) {
        console.warn('[Lantern] KaTeX auto-render notice:', err);
      }
      return;
    }

    // Chunk rendering across idle frames to prevent UI thread lockup on huge documents
    let idx = 0;
    const batchSize = 12;

    function renderNextBatch() {
      const end = Math.min(idx + batchSize, containers.length);
      for (; idx < end; idx++) {
        try {
          renderMathInElement(containers[idx], katexOptions);
        } catch (err) {
          console.warn('[Lantern] KaTeX chunk render notice:', err);
        }
      }
      if (idx < containers.length) {
        if (typeof window.requestIdleCallback === 'function') {
          window.requestIdleCallback(renderNextBatch, { timeout: 100 });
        } else {
          setTimeout(renderNextBatch, 0);
        }
      }
    }

    renderNextBatch();
  }

  // =========================================================================
  // 9. Code Copy Button
  // =========================================================================
  function initCodeCopy() {
    document.querySelectorAll('.lantern-prose pre').forEach(pre => {
      if (pre.querySelector('.lantern-copy-btn')) return;
      const btn = document.createElement('button');
      btn.className = 'lantern-btn lantern-btn-sm lantern-copy-btn';
      btn.textContent = 'Copy';
      btn.style.position = 'absolute';
      btn.style.top = '0.5rem';
      btn.style.right = '0.5rem';
      pre.style.position = 'relative';
      pre.appendChild(btn);

      btn.addEventListener('click', () => {
        const code = pre.querySelector('code');
        const text = code ? code.innerText : pre.innerText;
        navigator.clipboard.writeText(text).then(() => {
          btn.textContent = 'Copied!';
          window.lantern.toast('Code snippet copied to clipboard', 'info');
          setTimeout(() => {
            btn.textContent = 'Copy';
          }, 2000);
        });
      });
    });
  }

  // =========================================================================
  // 10. Responsive Plotly & Canvas Resize Coordinator
  // =========================================================================
  function initPlotlyResize() {
    let resizeTimer;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        if (window.Plotly) {
          document.querySelectorAll('.plotly-graph-div').forEach(el => {
            try {
              window.Plotly.Plots.resize(el);
            } catch (err) {}
          });
        }
      }, 100);
    }, { passive: true });
  }

  // DOMContentLoaded Initializer
  document.addEventListener('DOMContentLoaded', () => {
    initProgressBar();
    initHeadingAnchors();
    initSectionDotNav();
    initSliders();
    initSwitches();
    initSegments();
    initSelects();
    initSteppers();
    initTabs();
    initLightboxes();
    initCodeCopy();
    initPlotlyResize();
    initKaTeX();
  });
})();
