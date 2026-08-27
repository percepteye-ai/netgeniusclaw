/**
 * path-trace.js — Canvas component for hop-by-hop forwarding path visualization.
 *
 * Accepts PathTraceContent data model (source, destination, paths[], blackHole).
 * Renders hop-by-hop directed graph with per-hop labels, shows ECMP parallel
 * branches, and marks black hole failure points.
 */

import { buildA2UIEnvelope, buildErrorCard, createWarning } from '../lib/a2ui-renderer.js';
import { fetchPathTraceData } from '../lib/data-fetcher.js';

/**
 * Render a path trace visualization.
 *
 * @param {object} options
 * @param {string} options.source - Source IP address
 * @param {string} options.destination - Destination IP address
 * @param {object} [options.scope] - Scope filters
 * @param {string} [options.title] - Override title
 * @returns {object} A2UI JSON envelope
 */
async function renderPathTrace(options = {}) {
  const { source, destination, scope, title } = options;

  if (!source || !destination) {
    return buildErrorCard({
      title: 'Source and Destination Required',
      message: 'Path trace requires both a source and destination IP address.',
      suggestion: 'Try "trace path from 10.0.1.1 to 10.0.2.1".',
    });
  }

  const result = await fetchPathTraceData(source, destination);
  const { pathTrace, dataSources, warnings } = result;

  if (pathTrace.paths.length === 0 && !pathTrace.blackHole) {
    return buildErrorCard({
      title: 'Unable to Trace Path',
      message: `No forwarding path found from ${source} to ${destination}. Routing data may be unavailable.`,
      suggestion: 'Verify that routing data is available and both addresses are reachable.',
    });
  }

  const content = pathTrace;

  return buildA2UIEnvelope({
    component: 'path-trace',
    title: title || `Path Trace: ${source} -> ${destination}`,
    dataSources,
    scope: scope || {},
    warnings,
    content,
  });
}

/**
 * Render path trace as HTML for Canvas embedding.
 * @param {object} content - PathTraceContent
 * @param {Array} [allWarnings]
 * @returns {string} HTML string
 */
function renderPathTraceHTML(content, allWarnings = []) {
  const { source, destination, paths, blackHole } = content;
  const hasEcmp = paths.length > 1;

  let html = '<div class="path-trace">';

  // Header
  html += '<div class="path-trace__header">';
  html += '<div class="path-trace__endpoints">';
  html += `${escapeHtml(source)} <span class="path-trace__arrow">&rarr;</span> ${escapeHtml(destination)}`;
  html += '</div>';
  if (hasEcmp) {
    html += `<span class="path-trace__ecmp-badge">ECMP: ${paths.length} paths</span>`;
  }
  html += '</div>';

  // Paths
  html += '<div class="path-trace__paths">';

  for (const path of paths) {
    html += '<div class="path-trace__path">';

    if (hasEcmp) {
      html += `<div class="path-trace__path-label">${escapeHtml(path.id)}`;
      if (path.isEcmp) {
        html += ' <span class="path-trace__ecmp-indicator">Equal-cost path</span>';
      }
      html += '</div>';
    }

    // Hop sequence
    html += '<div class="path-trace__hops">';
    for (let i = 0; i < path.hops.length; i++) {
      const hop = path.hops[i];

      if (i > 0) {
        html += '<div class="path-trace__hop-arrow">&rarr;</div>';
      }

      html += '<div class="path-trace__hop">';
      html += `<div class="path-trace__hop-number">${hop.order}</div>`;
      html += `<div class="path-trace__hop-device">${escapeHtml(hop.device)}</div>`;

      if (hop.ingressInterface || hop.egressInterface) {
        html += '<div class="path-trace__hop-interfaces">';
        if (hop.ingressInterface) html += `in: ${escapeHtml(hop.ingressInterface)}`;
        if (hop.ingressInterface && hop.egressInterface) html += ' | ';
        if (hop.egressInterface) html += `out: ${escapeHtml(hop.egressInterface)}`;
        html += '</div>';
      }

      if (hop.nextHop) {
        html += `<div class="path-trace__hop-nexthop">NH: ${escapeHtml(hop.nextHop)}</div>`;
      }

      if (hop.action) {
        html += `<div class="path-trace__hop-action">${escapeHtml(hop.action)}</div>`;
      }

      html += '</div>';
    }
    html += '</div></div>';
  }

  // Black hole indicator
  if (blackHole) {
    html += '<div class="path-trace__blackhole">';
    html += '<div class="path-trace__blackhole-icon"></div>';
    html += '<div class="path-trace__blackhole-info">';
    html += '<div class="path-trace__blackhole-title">Black Hole Detected</div>';
    html += '<div class="path-trace__blackhole-detail">';
    html += `Last hop: <span class="path-trace__blackhole-device">${escapeHtml(blackHole.lastHop)}</span>`;
    if (blackHole.lastInterface) html += ` (${escapeHtml(blackHole.lastInterface)})`;
    html += `<br>Reason: ${escapeHtml(blackHole.reason)}`;
    html += '</div></div></div>';
  }

  html += '</div></div>';
  return html;
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

export {
  renderPathTrace,
  renderPathTraceHTML,
};
