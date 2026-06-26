/**
 * result.js — Prediction Result Charts
 * Renders: Radar chart, Gauge chart, Pie chart using Chart.js
 * Expects globals: RADAR_DATA, PROBABILITY, RISK_SCORE, IS_APPROVED
 */

'use strict';

document.addEventListener('DOMContentLoaded', function () {

  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const textColor  = isDark ? '#E6EDF3' : '#1A2332';
  const gridColor  = isDark ? 'rgba(255,255,255,.08)' : 'rgba(0,0,0,.07)';

  /* ══════════════════════════════════════════════
     1. RADAR CHART — Credit Profile
  ══════════════════════════════════════════════ */
  const radarCtx = document.getElementById('radarChart');
  if (radarCtx && typeof RADAR_DATA !== 'undefined') {
    new Chart(radarCtx, {
      type: 'radar',
      data: {
        labels: RADAR_DATA.labels,
        datasets: [{
          label: 'Credit Profile',
          data: RADAR_DATA.values,
          backgroundColor: IS_APPROVED
            ? 'rgba(46,125,50,.25)'
            : 'rgba(211,47,47,.25)',
          borderColor: IS_APPROVED ? '#2E7D32' : '#D32F2F',
          borderWidth: 2.5,
          pointBackgroundColor: IS_APPROVED ? '#2E7D32' : '#D32F2F',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 5,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        scales: {
          r: {
            min: 0, max: 100,
            ticks: {
              stepSize: 25,
              color: textColor,
              font: { size: 10, family: 'Poppins' },
              backdropColor: 'transparent',
            },
            grid:        { color: gridColor },
            angleLines:  { color: gridColor },
            pointLabels: {
              color: textColor,
              font: { size: 11, family: 'Poppins', weight: '600' },
            },
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: ctx => ` ${ctx.label}: ${ctx.raw}/100`
            }
          }
        }
      }
    });
  }

  /* ══════════════════════════════════════════════
     2. GAUGE CHART — Risk Score
     Rendered as a half-doughnut
  ══════════════════════════════════════════════ */
  const gaugeCtx = document.getElementById('gaugeChart');
  if (gaugeCtx && typeof RISK_SCORE !== 'undefined') {
    const risk = Math.min(Math.max(RISK_SCORE, 0), 100);

    // Colour based on risk level
    let gaugeColor;
    if (risk < 30)      gaugeColor = '#2E7D32';
    else if (risk < 55) gaugeColor = '#F57F17';
    else                gaugeColor = '#D32F2F';

    new Chart(gaugeCtx, {
      type: 'doughnut',
      data: {
        datasets: [{
          data: [risk, 100 - risk],
          backgroundColor: [gaugeColor, isDark ? '#30363D' : '#E0E7EF'],
          borderWidth: 0,
          circumference: 180,
          rotation: 270,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '75%',
        plugins: {
          legend: { display: false },
          tooltip: { enabled: false },
        }
      },
      plugins: [{
        id: 'gaugeLabel',
        afterDraw(chart) {
          const { ctx, width, height } = chart;
          ctx.save();
          ctx.font = `700 22px Poppins, sans-serif`;
          ctx.fillStyle = gaugeColor;
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(`${Math.round(risk)}`, width / 2, height * 0.72);
          ctx.font = `500 11px Poppins, sans-serif`;
          ctx.fillStyle = textColor;
          ctx.fillText('Risk Score', width / 2, height * 0.87);
          ctx.restore();
        }
      }]
    });
  }

  /* ══════════════════════════════════════════════
     3. PIE / DOUGHNUT — Decision Breakdown
  ══════════════════════════════════════════════ */
  const pieCtx = document.getElementById('pieChart');
  if (pieCtx && typeof PROBABILITY !== 'undefined') {
    const approvePct = Math.round(PROBABILITY * 100);
    const rejectPct  = 100 - approvePct;

    new Chart(pieCtx, {
      type: 'doughnut',
      data: {
        labels: ['Approval Probability', 'Rejection Risk'],
        datasets: [{
          data: [approvePct, rejectPct],
          backgroundColor: ['rgba(46,125,50,.85)', 'rgba(211,47,47,.85)'],
          borderColor:     ['#2E7D32', '#D32F2F'],
          borderWidth: 2,
          hoverOffset: 6,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        cutout: '65%',
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: ctx => ` ${ctx.label}: ${ctx.raw}%`
            }
          }
        }
      },
      plugins: [{
        id: 'centerLabel',
        afterDraw(chart) {
          const { ctx, width, height } = chart;
          ctx.save();
          ctx.font = `800 20px Poppins, sans-serif`;
          ctx.fillStyle = IS_APPROVED ? '#2E7D32' : '#D32F2F';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(`${approvePct}%`, width / 2, height / 2 - 6);
          ctx.font = `500 10px Poppins, sans-serif`;
          ctx.fillStyle = textColor;
          ctx.fillText('Approval', width / 2, height / 2 + 14);
          ctx.restore();
        }
      }]
    });
  }

});
