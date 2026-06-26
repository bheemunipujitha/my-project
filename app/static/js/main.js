/**
 * main.js — CreditPredict AI Core JavaScript
 * Handles: dark mode, counter animations, tooltips, page loader, scroll effects
 */

'use strict';

/* ══════════════════════════════════════════════════
   PAGE LOADER
══════════════════════════════════════════════════ */
(function initLoader() {
  const loader = document.getElementById('pageLoader');
  if (!loader) return;
  window.addEventListener('load', () => {
    setTimeout(() => {
      loader.classList.add('hidden');
      setTimeout(() => loader.remove(), 500);
    }, 400);
  });
})();


/* ══════════════════════════════════════════════════
   DARK MODE
══════════════════════════════════════════════════ */
const DarkMode = (() => {
  const KEY = 'creditpredict_theme';
  const html = document.documentElement;
  const iconEl = document.getElementById('darkModeIcon');
  const btnEl  = document.getElementById('darkModeToggle');

  function apply(isDark) {
    html.setAttribute('data-theme', isDark ? 'dark' : 'light');
    localStorage.setItem(KEY, isDark ? 'dark' : 'light');
    if (iconEl) {
      iconEl.className = isDark ? 'bi bi-sun-fill' : 'bi bi-moon-stars-fill';
    }
  }

  function init() {
    const saved = localStorage.getItem(KEY);
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    apply(saved ? saved === 'dark' : prefersDark);
    if (btnEl) {
      btnEl.addEventListener('click', () => {
        apply(html.getAttribute('data-theme') !== 'dark');
      });
    }
  }

  return { init };
})();

DarkMode.init();


/* ══════════════════════════════════════════════════
   BOOTSTRAP TOOLTIPS
══════════════════════════════════════════════════ */
function initTooltips() {
  const tooltipEls = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipEls.forEach(el => {
    if (typeof bootstrap !== 'undefined') {
      new bootstrap.Tooltip(el, { trigger: 'hover focus', delay: { show: 300, hide: 100 } });
    }
  });
}
document.addEventListener('DOMContentLoaded', initTooltips);


/* ══════════════════════════════════════════════════
   COUNTER ANIMATION
══════════════════════════════════════════════════ */
function animateCounters() {
  const counters = document.querySelectorAll('.counter[data-target]');
  if (!counters.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const el = entry.target;
      const target = parseFloat(el.dataset.target) || 0;
      const duration = 1500;
      const start = performance.now();
      const isFloat = !Number.isInteger(target);

      function update(now) {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        // Ease-out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = target * eased;
        el.textContent = isFloat ? current.toFixed(1) : Math.floor(current).toLocaleString();
        if (progress < 1) requestAnimationFrame(update);
        else el.textContent = isFloat ? target.toFixed(1) : target.toLocaleString();
      }

      requestAnimationFrame(update);
      observer.unobserve(el);
    });
  }, { threshold: 0.2 });

  counters.forEach(el => observer.observe(el));
}

document.addEventListener('DOMContentLoaded', animateCounters);


/* ══════════════════════════════════════════════════
   NAVBAR SCROLL EFFECT
══════════════════════════════════════════════════ */
(function navbarScroll() {
  const navbar = document.getElementById('mainNavbar');
  if (!navbar) return;
  window.addEventListener('scroll', () => {
    if (window.scrollY > 20) {
      navbar.style.boxShadow = '0 4px 30px rgba(15,76,129,.45)';
    } else {
      navbar.style.boxShadow = '0 2px 20px rgba(15,76,129,.35)';
    }
  }, { passive: true });
})();


/* ══════════════════════════════════════════════════
   AUTO-DISMISS FLASH ALERTS
══════════════════════════════════════════════════ */
(function autoFlash() {
  setTimeout(() => {
    document.querySelectorAll('.flash-alert').forEach(el => {
      if (typeof bootstrap !== 'undefined') {
        const alert = bootstrap.Alert.getOrCreateInstance(el);
        alert.close();
      } else {
        el.style.opacity = '0';
        setTimeout(() => el.remove(), 300);
      }
    });
  }, 5000);
})();


/* ══════════════════════════════════════════════════
   SMOOTH SCROLL FOR ANCHOR LINKS
══════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const target = document.querySelector(a.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
});


/* ══════════════════════════════════════════════════
   CARD HOVER ANIMATIONS (AOS-lite)
══════════════════════════════════════════════════ */
(function initAOS() {
  const els = document.querySelectorAll('[data-aos]');
  if (!els.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const delay = parseInt(el.dataset.aosDelay || 0, 10);
        setTimeout(() => el.classList.add('aos-animate'), delay);
        observer.unobserve(el);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

  // Inject base styles
  if (!document.getElementById('aos-style')) {
    const style = document.createElement('style');
    style.id = 'aos-style';
    style.textContent = `
      [data-aos] { opacity: 0; transition: opacity .5s ease, transform .5s ease; }
      [data-aos="fade-up"]    { transform: translateY(30px); }
      [data-aos="fade-right"] { transform: translateX(-30px); }
      [data-aos="fade-left"]  { transform: translateX(30px); }
      [data-aos="zoom-in"]    { transform: scale(.92); }
      [data-aos].aos-animate  { opacity: 1; transform: none; }
    `;
    document.head.appendChild(style);
  }

  els.forEach(el => observer.observe(el));
})();


/* ══════════════════════════════════════════════════
   PRINT HELPER
══════════════════════════════════════════════════ */
window.printReport = function () { window.print(); };
