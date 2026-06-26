/**
 * predict.js — Prediction Form Logic
 * Handles: live validation, section progress tracking,
 *          credit score bar, default toggle, submit animation
 */

'use strict';

document.addEventListener('DOMContentLoaded', function () {

  /* ── Elements ───────────────────────────────── */
  const form        = document.getElementById('predictionForm');
  const submitBtn   = document.getElementById('submitBtn');
  const scoreInput  = document.getElementById('creditScoreInput');
  const scoreThumb  = document.getElementById('scoreThumb');
  const progressBar = document.getElementById('overallProgress');
  const progressPct = document.getElementById('progressPct');

  /* ── Required fields list ───────────────────── */
  const REQUIRED = [
    'applicant_name','gender','age','marital_status','num_children',
    'education','annual_income','credit_score','employment_status',
    'loan_amount','loan_term','loan_purpose','prior_loans'
  ];

  /* ══════════════════════════════════════════════
     CREDIT SCORE VISUAL BAR
  ══════════════════════════════════════════════ */
  function updateScoreBar(val) {
    if (!scoreThumb) return;
    const score = Math.min(Math.max(parseInt(val) || 300, 300), 850);
    const pct   = ((score - 300) / 550) * 100;
    scoreThumb.style.left = `${pct}%`;
  }

  if (scoreInput) {
    scoreInput.addEventListener('input', () => updateScoreBar(scoreInput.value));
    updateScoreBar(scoreInput.value || 300);
  }

  /* ══════════════════════════════════════════════
     DEFAULT TOGGLE BUTTONS
  ══════════════════════════════════════════════ */
  const toggleNo  = document.getElementById('toggleNo');
  const toggleYes = document.getElementById('toggleYes');

  function setDefault(isDefault) {
    if (!toggleNo || !toggleYes) return;
    if (isDefault) {
      toggleYes.classList.add('active');
      toggleNo.classList.remove('active');
    } else {
      toggleNo.classList.add('active');
      toggleYes.classList.remove('active');
    }
  }

  if (toggleNo)  toggleNo.addEventListener('click',  () => setDefault(false));
  if (toggleYes) toggleYes.addEventListener('click', () => setDefault(true));

  /* ══════════════════════════════════════════════
     PROGRESS TRACKING
  ══════════════════════════════════════════════ */
  function updateProgress() {
    let filled = 0;
    REQUIRED.forEach(name => {
      const el = form ? form.querySelector(`[name="${name}"]`) : null;
      if (el && el.value.trim() !== '' && el.value !== '0' || (el && el.type === 'number' && el.value !== '')) {
        if (el.value.trim() !== '') filled++;
      }
    });
    const pct = Math.round((filled / REQUIRED.length) * 100);
    if (progressBar) progressBar.style.width = `${pct}%`;
    if (progressPct) progressPct.textContent = `${pct}%`;
    updateSidebarSteps();
  }

  /* ── Sidebar step highlight based on scroll ─── */
  const sections = ['personal-section','financial-section','credit-section','employment-section','loan-section'];

  function updateSidebarSteps() {
    sections.forEach((id, i) => {
      const sec   = document.getElementById(id);
      const step  = document.getElementById(`step-${i + 1}`);
      if (!sec || !step) return;

      const inputs = sec.querySelectorAll('input[required], select[required]');
      const filled = Array.from(inputs).every(el => el.value.trim() !== '');

      step.classList.toggle('completed', filled);
    });
  }

  function highlightActiveSection() {
    const scrollY = window.scrollY + 120;
    sections.forEach((id, i) => {
      const sec  = document.getElementById(id);
      const step = document.getElementById(`step-${i + 1}`);
      if (!sec || !step) return;
      const top = sec.offsetTop;
      const bot = top + sec.offsetHeight;
      if (scrollY >= top && scrollY < bot) {
        step.classList.add('active');
      } else {
        step.classList.remove('active');
      }
    });
  }

  window.addEventListener('scroll', highlightActiveSection, { passive: true });

  // Sidebar click to scroll
  sections.forEach((id, i) => {
    const step = document.getElementById(`step-${i + 1}`);
    if (step) {
      step.addEventListener('click', () => {
        const sec = document.getElementById(id);
        if (sec) sec.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    }
  });

  if (form) {
    form.addEventListener('input', updateProgress);
    form.addEventListener('change', updateProgress);
    updateProgress();
  }

  /* ══════════════════════════════════════════════
     LIVE VALIDATION
  ══════════════════════════════════════════════ */
  const VALIDATORS = {
    age:          v => v >= 18 && v <= 75,
    credit_score: v => v >= 300 && v <= 850,
    annual_income:v => v >= 5000,
    loan_amount:  v => v >= 500,
    num_children: v => v >= 0 && v <= 10,
    prior_loans:  v => v >= 0,
  };

  function validateField(input) {
    const name   = input.name;
    const val    = input.value.trim();
    const group  = input.closest('.input-group-custom');
    const errEl  = document.getElementById(`err-${name}`);
    let   valid  = true;
    let   msg    = '';

    if (input.required && val === '') {
      valid = false; msg = 'This field is required.';
    } else if (val !== '' && VALIDATORS[name]) {
      const num = parseFloat(val);
      if (!VALIDATORS[name](num)) {
        valid = false;
        msg = `Invalid value for ${name.replace(/_/g,' ')}.`;
      }
    }

    if (group) {
      group.classList.toggle('is-invalid', !valid);
      group.classList.toggle('is-valid', valid && val !== '');
    }
    if (errEl) errEl.textContent = valid ? '' : msg;
    return valid;
  }

  if (form) {
    form.querySelectorAll('input, select').forEach(el => {
      el.addEventListener('blur', () => validateField(el));
      el.addEventListener('input', () => {
        if (el.closest('.input-group-custom')?.classList.contains('is-invalid')) {
          validateField(el);
        }
      });
    });
  }

  /* ══════════════════════════════════════════════
     FORM SUBMIT ANIMATION
  ══════════════════════════════════════════════ */
  if (form && submitBtn) {
    form.addEventListener('submit', function (e) {
      // Run validation on all required fields
      let allValid = true;
      form.querySelectorAll('input[required], select[required]').forEach(el => {
        if (!validateField(el)) allValid = false;
      });

      if (!allValid) {
        e.preventDefault();
        // Scroll to first error
        const firstErr = form.querySelector('.input-group-custom.is-invalid');
        if (firstErr) firstErr.scrollIntoView({ behavior: 'smooth', block: 'center' });
        return;
      }

      // Show loading state
      const textEl    = submitBtn.querySelector('.submit-text');
      const loadingEl = submitBtn.querySelector('.submit-loading');
      if (textEl && loadingEl) {
        textEl.classList.add('d-none');
        loadingEl.classList.remove('d-none');
      }
      submitBtn.disabled = true;
    });
  }

  /* ══════════════════════════════════════════════
     SELECT DROPDOWN ANIMATION
  ══════════════════════════════════════════════ */
  document.querySelectorAll('.form-select-custom').forEach(sel => {
    sel.addEventListener('change', function () {
      this.style.transform = 'scale(1.01)';
      setTimeout(() => this.style.transform = '', 150);
    });
  });

});
