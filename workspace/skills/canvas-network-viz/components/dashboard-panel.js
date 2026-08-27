/**
 * dashboard-panel.js — Canvas component for device/site health dashboards.
 *
 * Accepts DashboardContent data model (panels[], deviceSummary).
 * Renders each DashboardPanel by type (gauge, counter, status-list, bar, sparkline).
 * Applies ThresholdConfig coloring and renders StatusItem lists for BGP/OSPF.
 *
 * Handles: multi-device site dashboards (T020), graceful degradation (T021).
 */

import { classifyHealth, getHealthColor } from '../lib/color-scale.js';
import { buildA2UIEnvelope, buildErrorCard, createWarning } from '../lib/a2ui-renderer.js';
import { fetchDashboardData } from '../lib/data-fetcher.js';

/**
 * Render a dashboard panel visualization.
 *
 * @param {object} options
 * @param {string} options.target - Device hostname or site name
 * @param {boolean} [options.isSite=false] - Site-level dashboard
 * @param {object} [options.scope] - Scope filters
 * @param {string} [options.title] - Override title
 * @returns {object} A2UI JSON envelope
 */
async function renderDashboardPanel(options = {}) {
  const { target, isSite = false, scope, title } = options;

  if (!target) {
    return buildErrorCard({
      title: 'No Target Specified',
      message: 'Dashboard visualization requires a device or site target.',
      suggestion: 'Try "show health dashboard for R1" or "show site dashboard for Site-A".',
    });
  }

  const result = await fetchDashboardData(target, isSite);
  const { panels, deviceSummary, dataSources, warnings } = result;

  // T021: Graceful degradation
  if (panels.length === 0) {
    const allUnavailable = dataSources.every(ds => ds.status === 'unavailable');
    if (allUnavailable) {
      return buildErrorCard({
        title: 'Dashboard Data Unavailable',
        message: `No data sources responded for ${target}. All MCP servers (pyATS, Grafana, Prometheus) are unreachable.`,
        suggestion: 'Check MCP server connectivity and try again.',
      });
    }

    warnings.push(createWarning('warning',
      `No metric data available for ${target}. Some data sources may be unavailable.`,
      'dashboard'));
  }

  const content = {
    panels,
    deviceSummary,
  };

  return buildA2UIEnvelope({
    component: 'dashboard-panel',
    title: title || (isSite ? `Site Dashboard: ${target}` : `Health Dashboard: ${target}`),
    dataSources,
    scope: scope || { devices: isSite ? [] : [target], sites: isSite ? [target] : [] },
    warnings,
    content,
  });
}

/**
 * Render the dashboard as HTML for Canvas embedding.
 * @param {object} content - DashboardContent
 * @param {Array} [allWarnings] - Warning[]
 * @returns {string} HTML string
 */
function renderDashboardHTML(content, allWarnings = []) {
  const { panels, deviceSummary } = content;

  let html = '<div class="dashboard-panel">';

  // Header
  if (deviceSummary) {
    html += `<div class="dashboard-panel__header">${escapeHtml(deviceSummary)}</div>`;
  }

  // Warnings
  for (const w of allWarnings) {
    if (w.level === 'warning' || w.level === 'error') {
      html += `<div class="dashboard-warning">${escapeHtml(w.message)}</div>`;
    }
  }

  // Panel grid
  html += '<div class="dashboard-panel__grid">';

  for (const panel of panels) {
    html += renderPanelCard(panel);
  }

  html += '</div></div>';
  return html;
}

/**
 * Render a single panel card.
 * @param {object} panel - DashboardPanel
 * @returns {string} HTML string
 */
function renderPanelCard(panel) {
  let html = '<div class="dashboard-card">';
  html += `<div class="dashboard-card__title">${escapeHtml(panel.title)}</div>`;

  switch (panel.type) {
    case 'gauge':
      html += renderGauge(panel);
      break;
    case 'counter':
      html += renderCounter(panel);
      break;
    case 'status-list':
      html += renderStatusList(panel);
      break;
    case 'bar':
      html += renderBarChart(panel);
      break;
    case 'sparkline':
      html += renderSparkline(panel);
      break;
    default:
      html += renderCounter(panel);
  }

  html += '</div>';
  return html;
}

/**
 * Render a gauge panel.
 */
function renderGauge(panel) {
  const value = typeof panel.value === 'number' ? panel.value : parseFloat(panel.value) || 0;
  const health = panel.threshold
    ? classifyHealth(value)
    : 'healthy';

  const pct = Math.min(100, Math.max(0, value));

  return `<div class="dashboard-gauge dashboard-gauge--${health}">
    <div class="dashboard-gauge__value">${value}<span class="dashboard-gauge__unit">${escapeHtml(panel.unit || '')}</span></div>
    <div class="dashboard-gauge__bar"><div class="dashboard-gauge__fill" style="width:${pct}%"></div></div>
  </div>`;
}

/**
 * Render a counter panel.
 */
function renderCounter(panel) {
  return `<div class="dashboard-counter">
    <div class="dashboard-counter__value">${escapeHtml(String(panel.value))}${panel.unit ? ` <span class="dashboard-gauge__unit">${escapeHtml(panel.unit)}</span>` : ''}</div>
  </div>`;
}

/**
 * Render a status list panel.
 */
function renderStatusList(panel) {
  const items = panel.items || [];
  let html = `<div class="dashboard-counter"><div class="dashboard-counter__value">${escapeHtml(String(panel.value))}</div></div>`;
  html += '<ul class="dashboard-status-list">';

  for (const item of items) {
    const statusClass = `dashboard-status-item--${item.status}`;
    html += `<li class="dashboard-status-item ${statusClass}">`;
    html += '<span class="dashboard-status-item__indicator"></span>';
    html += `<span class="dashboard-status-item__name">${escapeHtml(item.name)}</span>`;
    if (item.detail) {
      html += `<span class="dashboard-status-item__detail">${escapeHtml(item.detail)}</span>`;
    }
    html += '</li>';
  }

  html += '</ul>';
  return html;
}

/**
 * Render a bar chart panel.
 */
function renderBarChart(panel) {
  const value = typeof panel.value === 'number' ? panel.value : parseFloat(panel.value) || 0;
  const health = panel.threshold ? classifyHealth(value) : 'healthy';
  const color = getHealthColor(health);
  const pct = Math.min(100, Math.max(0, value));

  return `<div class="dashboard-gauge dashboard-gauge--${health}">
    <div class="dashboard-gauge__value">${value}<span class="dashboard-gauge__unit">${escapeHtml(panel.unit || '')}</span></div>
    <div class="dashboard-gauge__bar"><div class="dashboard-gauge__fill" style="width:${pct}%; background:${color}"></div></div>
  </div>`;
}

/**
 * Render a sparkline panel.
 */
function renderSparkline(panel) {
  // Sparklines would render a miniature line chart; placeholder for Canvas SVG
  return `<div class="dashboard-sparkline">
    <div class="dashboard-counter__value">${escapeHtml(String(panel.value))}${panel.unit ? ` ${escapeHtml(panel.unit)}` : ''}</div>
  </div>`;
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

export {
  renderDashboardPanel,
  renderDashboardHTML,
};
