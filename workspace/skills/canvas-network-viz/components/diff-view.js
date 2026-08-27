/**
 * diff-view.js — Canvas component for configuration/route/ACL diff visualization.
 *
 * Accepts DiffContent data model (diffType, device, hunks[]).
 * Renders DiffHunk sections with headers and DiffLine entries with
 * type-based coloring (added green, removed red, context neutral).
 */

import { buildA2UIEnvelope, buildErrorCard, createWarning } from '../lib/a2ui-renderer.js';
import { fetchDiffData } from '../lib/data-fetcher.js';

/**
 * Render a diff view visualization.
 *
 * @param {object} options
 * @param {string} options.device - Device hostname
 * @param {'config'|'routing'|'acl'} options.diffType - Type of diff
 * @param {object} [options.scope] - Scope filters
 * @param {string} [options.title] - Override title
 * @returns {object} A2UI JSON envelope
 */
async function renderDiffView(options = {}) {
  const { device, diffType = 'config', scope, title } = options;

  if (!device) {
    return buildErrorCard({
      title: 'No Device Specified',
      message: 'Diff visualization requires a device target.',
      suggestion: 'Try "show config diff for R1" or "show routing changes for R2".',
    });
  }

  const result = await fetchDiffData(device, diffType);
  const { diff, dataSources, warnings } = result;

  if (!diff.hunks || diff.hunks.length === 0) {
    warnings.push(createWarning('info',
      `No ${diffType} differences detected for ${device}. Current state matches previous snapshot.`,
      'diff'));
  }

  const content = diff;

  const typeLabels = { config: 'Configuration', routing: 'Routing Table', acl: 'Access Control Lists' };

  return buildA2UIEnvelope({
    component: 'diff-view',
    title: title || `${typeLabels[diffType] || 'Config'} Diff: ${device}`,
    dataSources,
    scope: scope || { devices: [device] },
    warnings,
    content,
  });
}

/**
 * Render diff view as HTML for Canvas embedding.
 * @param {object} content - DiffContent
 * @param {Array} [allWarnings]
 * @returns {string} HTML string
 */
function renderDiffHTML(content, allWarnings = []) {
  const { diffType, device, before, after, hunks } = content;

  let html = '<div class="diff-view">';

  // Header
  html += '<div class="diff-view__header">';
  html += `<span class="diff-view__device">${escapeHtml(device)}</span>`;
  html += `<span class="diff-view__type">${escapeHtml(diffType)}</span>`;
  html += '<div class="diff-view__labels">';
  if (before) html += `<span class="diff-view__label-before">${escapeHtml(before)}</span>`;
  if (after) html += `<span class="diff-view__label-after">${escapeHtml(after)}</span>`;
  html += '</div></div>';

  // Content
  html += '<div class="diff-view__content">';

  if (!hunks || hunks.length === 0) {
    html += '<div class="diff-view__no-changes">No differences detected</div>';
  } else {
    for (const hunk of hunks) {
      html += '<div class="diff-hunk">';
      if (hunk.header) {
        html += `<div class="diff-hunk__header">${escapeHtml(hunk.header)}</div>`;
      }

      for (const line of hunk.lines) {
        html += `<div class="diff-line diff-line--${line.type}">`;
        html += `<span class="diff-line__number">${line.lineNumber || ''}</span>`;
        html += '<span class="diff-line__indicator"></span>';
        html += `<span class="diff-line__content">${escapeHtml(line.content)}</span>`;
        html += '</div>';
      }

      html += '</div>';
    }
  }

  html += '</div></div>';
  return html;
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

export {
  renderDiffView,
  renderDiffHTML,
};
