/**
 * health-scorecard.js — Canvas component for aggregated health scorecards.
 *
 * Accepts ScorecardContent data model (level, entries[]).
 * Renders ScorecardEntry rows with overall health color, composite score,
 * HealthIndicator badges, and drill-down toggle from site to device level.
 */

import { getHealthColor } from '../lib/color-scale.js';
import { buildA2UIEnvelope, buildErrorCard, createWarning } from '../lib/a2ui-renderer.js';
import { fetchScorecardData } from '../lib/data-fetcher.js';

/**
 * Render a health scorecard visualization.
 *
 * @param {object} options
 * @param {string} options.target - Device or site name
 * @param {'site'|'device'} [options.level='device'] - Scorecard level
 * @param {object} [options.scope] - Scope filters
 * @param {string} [options.title] - Override title
 * @returns {object} A2UI JSON envelope
 */
async function renderHealthScorecard(options = {}) {
  const { target, level = 'device', scope, title } = options;

  if (!target) {
    return buildErrorCard({
      title: 'No Target Specified',
      message: 'Health scorecard requires a device or site target.',
      suggestion: 'Try "show health scorecard for Site-A" or "show device health for R1".',
    });
  }

  const result = await fetchScorecardData(target, level);
  const { scorecard, dataSources, warnings } = result;

  if (scorecard.entries.length === 0) {
    return buildErrorCard({
      title: 'No Health Data Available',
      message: `No health data found for ${target}. The device or site may not exist, or health metrics are unavailable.`,
      suggestion: 'Verify the device/site name and check that monitoring data sources are connected.',
    });
  }

  const content = scorecard;

  return buildA2UIEnvelope({
    component: 'health-scorecard',
    title: title || (level === 'site'
      ? `Site Health Scorecard: ${target}`
      : `Device Health: ${target}`),
    dataSources,
    scope: scope || (level === 'site' ? { sites: [target] } : { devices: [target] }),
    warnings,
    content,
  });
}

/**
 * Render health scorecard as HTML for Canvas embedding.
 * @param {object} content - ScorecardContent
 * @param {Array} [allWarnings]
 * @returns {string} HTML string
 */
function renderScorecardHTML(content, allWarnings = []) {
  const { level, entries } = content;

  let html = '<div class="health-scorecard">';

  // Header
  html += `<div class="health-scorecard__header">${level === 'site' ? 'Site Health Overview' : 'Device Health'}</div>`;

  // Entries
  html += '<div class="health-scorecard__grid">';

  for (const entry of entries) {
    html += '<div class="health-scorecard__entry">';

    // Health indicator circle
    html += `<span class="health-scorecard__health-indicator health-scorecard__health-indicator--${entry.overallHealth}"></span>`;

    // Name
    html += `<span class="health-scorecard__name">${escapeHtml(entry.name)}</span>`;

    // Indicator badges
    html += '<div class="health-scorecard__indicators">';
    for (const indicator of entry.indicators) {
      html += `<span class="health-scorecard__badge health-scorecard__badge--${indicator.status}">`;
      html += '<span class="health-scorecard__badge-dot"></span>';
      html += `${escapeHtml(indicator.name)}: ${escapeHtml(indicator.value)}`;
      html += '</span>';
    }
    html += '</div>';

    // Score
    html += `<span class="health-scorecard__score health-scorecard__score--${entry.overallHealth}">`;
    html += `${entry.score}<span class="health-scorecard__score-label">/100</span>`;
    html += '</span>';

    // Drill-down indicator
    if (entry.drillDown) {
      html += '<span class="health-scorecard__drilldown-icon">&rsaquo;</span>';
    }

    html += '</div>';
  }

  html += '</div></div>';
  return html;
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

export {
  renderHealthScorecard,
  renderScorecardHTML,
};
