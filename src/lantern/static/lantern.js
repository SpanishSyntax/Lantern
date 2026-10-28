/**
 * Lantern Core Client Runtime
 * Frost's Interactive Explainer & Simulation Dashboard Engine
 */

(function () {
  'use strict';

  // Initialize KaTeX Math rendering
  function initKaTeX() {
    if (typeof renderMathInElement === 'function') {
      try {
        renderMathInElement(document.body, {
          delimiters: [
            { left: '$$', right: '$$', display: true },
            { left: '$', right: '$', display: false },
            { left: '\\(', right: '\\)', display: false },
            { left: '\\[', right: '\\]', display: true }
          ],
          throwOnError: false,
          ignoredTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
        });
      } catch (err) {
        console.warn('[Lantern] KaTeX auto-render notice:', err);
      }
    }
  }

  // Copy code blocks
  function initCodeCopy() {
    document.querySelectorAll('.lantern-prose pre').forEach(pre => {
      if (pre.querySelector('.lantern-copy-btn')) return;
      const btn = document.createElement('button');
      btn.className = 'lantern-copy-btn';
      btn.textContent = 'Copy';
      btn.style.position = 'absolute';
      btn.style.top = '0.5rem';
      btn.style.right = '0.5rem';
      btn.style.fontSize = '0.75rem';
      btn.style.padding = '0.2rem 0.5rem';
      btn.style.borderRadius = '4px';
      btn.style.background = 'var(--bg-surface)';
      btn.style.border = '1px solid var(--border-medium)';
      btn.style.color = 'var(--text-secondary)';
      btn.style.cursor = 'pointer';

      pre.style.position = 'relative';
      pre.appendChild(btn);

      btn.addEventListener('click', () => {
        const code = pre.querySelector('code');
        const text = code ? code.innerText : pre.innerText;
        navigator.clipboard.writeText(text).then(() => {
          btn.textContent = 'Copied!';
          btn.style.color = 'var(--cyan)';
          setTimeout(() => {
            btn.textContent = 'Copy';
            btn.style.color = 'var(--text-secondary)';
          }, 2000);
        });
      });
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    initKaTeX();
    initCodeCopy();
  });
})();
