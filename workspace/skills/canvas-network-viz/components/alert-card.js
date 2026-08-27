/**
 * alert-card.js — Canvas component for alert/incident visualization.
 *
 * Accepts AlertContent data model (summary, alerts[], filter, unfilteredCount).
 * Renders severity summary counts at top, individual AlertCard entries sorted
 * by severity, and handles the "all clear" state.
 *
 * Handles: alert filtering (T026).
 */

import { getSeverityColor, getSeverityBgColor } from '../lib/color-scale.js';
import { filterAlerts, describeFilters, hasActiveFilters } from '../lib/filter-engine.js';
import { buildA2UIEnvelope, buildErrorCard, createWarning } from '../lib/a2ui-renderer.js';
import { fetchAlertData } from '../lib/data-fetcher.js';

/**
 * Render an alert card visualization.
 *
 * @param {object} options
 * @param {object} [options.scope] - Scope filters (severity, device, time)
 * @param {string} [options.title] - Override title
 * @returns {object} A2UI JSON envelope
 */
async function renderAlertCard(options = {}) {
  const { scope, title } = options;

  const result = await fetchAlertData();
  let { alerts, dataSources, warnings } = result;
  const unfilteredCount = alerts.length;

  // T026: Apply filtering
  let filterDescription = null;
  if (scope && hasActiveFilters(scope)) {
    alerts = filterAlerts(alerts, scope);
    filterDescription = describeFilters(scope);
  }

  // Build severity summary
  const summary = {
    critical: alerts.filter(a => a.severity === 'critical').length,
    warning: alerts.filter(a => a.severity === 'warning').length,
    info: alerts.filter(a => a.severity === 'info').length,
    total: alerts.length,
  };

  const content = {
    summary,
    alerts,
    filter: filterDescription,
    unfilteredCount: hasActiveFilters(scope) ? unfilteredCount : undefined,
  };

  return buildA2UIEnvelope({
    component: 'alert-card',
    title: title || 'Active Alerts',
    dataSources,
    scope: scope || {},
    warnings,
    content,
  });
}

/**
 * Render alert cards as HTML for Canvas embedding.
 * @param {object} content - AlertContent
 * @param {Array} [allWarnings]
 * @returns {string} HTML string
 */
function renderAlertHTML(content, allWarnings = []) {
  const { summary, alerts, filter, unfilteredCount } = content;

  let html = '<div class="alert-card-container">';

  // Severity summary bar
  html += '<div class="alert-summary">';
  html += `<div class="alert-summary__item"><span class="alert-summary__badge alert-summary__badge--critical">${summary.critical}</span><span class="alert-summary__label">Critical</span></div>`;
  html += `<div class="alert-summary__item"><span class="alert-summary__badge alert-summary__badge--warning">${summary.warning}</span><span class="alert-summary__label">Warning</span></div>`;
  html += `<div class="alert-summary__item"><span class="alert-summary__badge alert-summary__badge--info">${summary.info}</span><span class="alert-summary__label">Info</span></div>`;
  html += `<div class="alert-summary__total">${summary.total} total`;
  if (unfilteredCount !== undefined && unfilteredCount !== summary.total) {
    html += ` (of ${unfilteredCount})`;
  }
  html += '</div></div>';

  // Filter indicator
  if (filter) {
    html += `<div class="alert-filter">${escapeHtml(filter)}</div>`;
  }

  // All-clear state
  if (alerts.length === 0) {
    html += '<div class="alert-all-clear">';
    html += '<div class="alert-all-clear__icon"></div>';
    html += '<div class="alert-all-clear__message">All Clear</div>';
    html += '<div class="alert-all-clear__detail">No active alerts at this time.</div>';
    html += '</div>';
  } else {
    // Alert card list
    html += '<div class="alert-card-list">';
    for (const alert of alerts) {
      html += renderSingleAlertCard(alert);
    }
    html += '</div>';
  }

  html += '</div>';
  return html;
}

/**
 * Render a single alert card.
 */
function renderSingleAlertCard(alert) {
  let html = `<div class="alert-card alert-card--${alert.severity}">`;
  html += '<div class="alert-card__header">';
  html += `<span class="alert-card__severity">${escapeHtml(alert.severity)}</span>`;
  html += `<span class="alert-card__name">${escapeHtml(alert.name)}</span>`;
  html += `<span class="alert-card__source">${escapeHtml(alert.source)}</span>`;
  html += '</div>';

  if (alert.description) {
    html += `<div class="alert-card__body">${escapeHtml(alert.description)}</div>`;
  }

  html += '<div class="alert-card__meta">';
  if (alert.device) {
    html += `<span>Device: ${escapeHtml(alert.device)}</span>`;
  }
  if (alert.interface) {
    html += `<span>Interface: ${escapeHtml(alert.interface)}</span>`;
  }
  if (alert.triggeredAt) {
    html += `<span>Triggered: ${escapeHtml(alert.triggeredAt)}</span>`;
  }
  html += '</div>';

  html += '</div>';
  return html;
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

export {
  renderAlertCard,
  renderAlertHTML,
};
