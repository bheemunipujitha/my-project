/**
 * dashboard.js — Analytics Dashboard Charts
 * Renders all Chart.js visualizations for the analytics dashboard.
 * Expects global: CHART_DATA, STATS
 */

'use strict';

document.addEventListener('DOMContentLoaded', function () {

  if (typeof CHART_DATA === 'undefined' || typeof STATS === 'undefined') return;

  const isDark    = document.documentElement.getAttribute('data-theme') === 'dark';
  const textColor = isDark ? '#E6EDF3' : '#546E7A';
  const gridColor = isDark ? 'rgba(255,255,255,.06)' : 'rgba(0,0,0,.06)';

  /* ── Shared defaults ───────────────────────────── */
  Chart.defaults.font.family = 'Poppins, sans-serif';
  Chart.defaults.font.size   = 12;
  Chart.defaults.color       = textColor;

  /* ══════════════════════════════════════════════
     1. DAILY TREND — Line Chart
  ══════════════════════════════════════════════ */
  const trendCtx = document.getElementById('trendChart');
  if (trendCtx && CHART_DATA.daily_trend) {
    const d = CHART_DATA.daily_trend;
    new Chart(trendCtx, {
      type: 'line',
      data: {
        labels: d.labels,
        datasets: [
          {
            label: 'Approved',
            data: d.approved,
            borderColor: '#2E7D32',
            backgroundColor: 'rgba(46,125,50,.12)',
            borderWidth: 2.5,
            pointRadius: 3,
            pointHoverRadius: 6,
            tension: 0.4,
            fill: true,
          },
          {
            label: 'Rejected',
            data: d.rejected,
            borderColor: '#D32F2F',
            backgroundColor: 'rgba(211,47,47,.1)',
            borderWidth: 2.5,
            pointRadius: 3,
            pointHoverRadius: 6,
            tension: 0.4,
            fill: true,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: { bodyFont: { family: 'Poppins' } }
        },
        scales: {
          x: {
            grid: { color: gridColor, drawBorder: false },
            ticks: {
              maxTicksLimit: 10,
              maxRotation: 0,
              color: textColor,
            }
          },
          y: {
            beginAtZero: true,
            grid: { color: gridColor, drawBorder: false },
            ticks: { color: textColor, stepSize: 1 }
          }
        }
      }
    });
  }

  /* ══════════════════════════════════════════════
     2. SPLIT — Doughnut
  ══════════════════════════════════════════════ */
  const splitCtx = document.getElementById('splitChart');
  if (splitCtx && STATS) {
    new Chart(splitCtx, {
      type: 'doughnut',
      data: {
        labels: ['Approved', 'Rejected'],
        datasets: [{
          data: [STATS.approved || 0, STATS.rejected || 0],
          backgroundColor: ['rgba(46,125,50,.85)', 'rgba(211,47,47,.85)'],
          borderColor: ['#2E7D32', '#D32F2F'],
          borderWidth: 2,
          hoverOffset: 8,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        cutout: '68%',
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: ctx => ` ${ctx.label}: ${ctx.raw} (${((ctx.raw/(STATS.total||1))*100).toFixed(1)}%)`
            }
          }
        }
      },
      plugins: [{
        id: 'centerText',
        afterDraw(chart) {
          const { ctx, width, height } = chart;
          ctx.save();
          ctx.font = '700 18px Poppins';
          ctx.fillStyle = '#0F4C81';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(STATS.total || 0, width / 2, height / 2 - 6);
          ctx.font = '500 10px Poppins';
          ctx.fillStyle = textColor;
          ctx.fillText('Total', width / 2, height / 2 + 12);
          ctx.restore();
        }
      }]
    });
  }

  /* ══════════════════════════════════════════════
     3. CREDIT SCORE DISTRIBUTION — Bar
  ══════════════════════════════════════════════ */
  const scoreCtx = document.getElementById('scoreDistChart');
  if (scoreCtx && CHART_DATA.credit_score_buckets) {
    const buckets = CHART_DATA.credit_score_buckets;
    new Chart(scoreCtx, {
      type: 'bar',
      data: {
        labels: Object.keys(buckets),
        datasets: [{
          label: 'Applicants',
          data: Object.values(buckets),
          backgroundColor: [
            'rgba(211,47,47,.8)',
            'rgba(245,127,23,.8)',
            'rgba(249,168,37,.8)',
            'rgba(2,119,189,.8)',
            'rgba(46,125,50,.8)',
            'rgba(27,94,32,.8)',
          ],
          borderRadius: 6,
          borderSkipped: false,
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { color: textColor } },
          y: { beginAtZero: true, grid: { color: gridColor }, ticks: { color: textColor, stepSize: 1 } }
        }
      }
    });
  }

  /* ══════════════════════════════════════════════
     4. EMPLOYMENT STATUS — Polar Area
  ══════════════════════════════════════════════ */
  const empCtx = document.getElementById('employmentChart');
  if (empCtx && CHART_DATA.employment) {
    const emp = CHART_DATA.employment;
    new Chart(empCtx, {
      type: 'polarArea',
      data: {
        labels: Object.keys(emp),
        datasets: [{
          data: Object.values(emp),
          backgroundColor: [
            'rgba(15,76,129,.75)',
            'rgba(46,125,50,.75)',
            'rgba(245,127,23,.75)',
            'rgba(211,47,47,.75)',
          ],
          borderColor: ['#0F4C81','#2E7D32','#F57F17','#D32F2F'],
          borderWidth: 1.5,
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: true,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { font: { size: 11 }, color: textColor, boxWidth: 12 }
          }
        }
      }
    });
  }

  /* ══════════════════════════════════════════════
     5. LOAN PURPOSE — Horizontal Bar
  ══════════════════════════════════════════════ */
  const purposeCtx = document.getElementById('purposeChart');
  if (purposeCtx && CHART_DATA.loan_purpose) {
    const p = CHART_DATA.loan_purpose;
    const colors = ['#0F4C81','#1565C0','#2E7D32','#F57F17','#D32F2F','#0277BD','#546E7A'];
    new Chart(purposeCtx, {
      type: 'bar',
      data: {
        labels: Object.keys(p),
        datasets: [{
          label: 'Count',
          data: Object.values(p),
          backgroundColor: colors.map(c => c + 'CC'),
          borderColor: colors,
          borderWidth: 1.5,
          borderRadius: 6,
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { beginAtZero: true, grid: { color: gridColor }, ticks: { color: textColor } },
          y: { grid: { display: false }, ticks: { color: textColor } }
        }
      }
    });
  }

  /* ══════════════════════════════════════════════
     REFRESH BUTTON
  ══════════════════════════════════════════════ */
  const refreshBtn = document.getElementById('refreshCharts');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', function () {
      const icon = this.querySelector('i');
      if (icon) { icon.style.transform = 'rotate(360deg)'; icon.style.transition = 'transform .5s'; }
      fetch('/dashboard/api/stats')
        .then(r => r.json())
        .catch(() => null)
        .finally(() => {
          setTimeout(() => { if (icon) icon.style.transform = ''; }, 600);
        });
    });
  }

});
