/**
 * change-timeline.js — Canvas component for ServiceNow change request timelines.
 *
 * Accepts TimelineContent data model (changeRequests[]).
 * Renders each ChangeRequestTimeline as a horizontal stage progression.
 *
 * Handles: multi-CR summary view (T031), ServiceNow unavailable (T032).
 */

import { buildA2UIEnvelope, buildErrorCard, createWarning } from '../lib/a2ui-renderer.js';
import { fetchChangeData } from '../lib/data-fetcher.js';

/**
 * Render a change timeline visualization.
 *
 * @param {object} options
 * @param {string} [options.crNumber] - Specific CR number, or null for all active
 * @param {object} [options.scope] - Scope filters
 * @param {string} [options.title] - Override title
 * @returns {object} A2UI JSON envelope
 */
async function renderChangeTimeline(options = {}) {
  const { crNumber, scope, title } = options;

  const result = await fetchChangeData(crNumber);
  const { changeRequests, dataSources, warnings } = result;

  // T032: ServiceNow unavailable handling
  const snSource = dataSources.find(ds => ds.server === 'servicenow');
  if (snSource && snSource.status === 'unavailable') {
    return buildErrorCard({
      title: 'ServiceNow Unavailable',
      message: 'Unable to retrieve change request data. The ServiceNow MCP server is unreachable.',
      suggestion: 'Check ServiceNow MCP server connectivity and credentials, then retry.',
    });
  }

  if (changeRequests.length === 0) {
    return buildErrorCard({
      title: crNumber ? `Change Request ${crNumber} Not Found` : 'No Active Change Requests',
      message: crNumber
        ? `No change request found with number ${crNumber}.`
        : 'There are no active change requests at this time.',
      suggestion: crNumber
        ? 'Verify the CR number and try again.'
        : 'This is a good state — no pending changes.',
    });
  }

  const content = {
    changeRequests,
  };

  return buildA2UIEnvelope({
    component: 'change-timeline',
    title: title || (crNumber ? `Change Request: ${crNumber}` : 'Active Change Requests'),
    dataSources,
    scope: scope || {},
    warnings,
    content,
  });
}

/**
 * Render change timelines as HTML for Canvas embedding.
 * @param {object} content - TimelineContent
 * @param {Array} [allWarnings]
 * @returns {string} HTML string
 */
function renderTimelineHTML(content, allWarnings = []) {
  const { changeRequests } = content;
  const isMulti = changeRequests.length > 1;

  let html = '<div class="change-timeline-container">';

  for (const cr of changeRequests) {
    const compactClass = isMulti ? ' change-timeline--compact' : '';
    html += `<div class="change-timeline${compactClass}">`;

    // Header
    html += '<div class="change-timeline__header">';
    html += `<span class="change-timeline__cr-number">${escapeHtml(cr.crNumber)}</span>`;
    html += `<span class="change-timeline__description">${escapeHtml(cr.description)}</span>`;
    html += `<span class="change-timeline__status change-timeline__status--${cr.status}">${escapeHtml(cr.status)}</span>`;
    html += '</div>';

    // Stage timeline
    html += '<div class="change-timeline__stages">';
    for (let i = 0; i < cr.stages.length; i++) {
      const stage = cr.stages[i];

      // Connector before stage (except first)
      if (i > 0) {
        let connectorClass = 'change-timeline__connector';
        const prevStage = cr.stages[i - 1];
        if (prevStage.status === 'completed') connectorClass += ' change-timeline__connector--completed';
        if (stage.status === 'active') connectorClass += ' change-timeline__connector--active';
        html += `<div class="${connectorClass}"></div>`;
      }

      html += `<div class="change-timeline__stage change-timeline__stage--${stage.status}">`;
      html += '<div class="change-timeline__stage-node"></div>';
      html += `<span class="change-timeline__stage-label">${escapeHtml(stage.name)}</span>`;
      html += '</div>';
    }
    html += '</div>';

    // Metadata
    html += '<div class="change-timeline__meta">';
    if (cr.assignee) {
      html += `<div class="change-timeline__meta-item"><span class="change-timeline__meta-label">Assignee:</span>${escapeHtml(cr.assignee)}</div>`;
    }
    if (cr.scheduledWindow) {
      html += `<div class="change-timeline__meta-item"><span class="change-timeline__meta-label">Window:</span>${escapeHtml(cr.scheduledWindow.start)} - ${escapeHtml(cr.scheduledWindow.end)}</div>`;
    }
    html += '</div>';

    // Rejection / rollback reason
    if (cr.rejectionReason && (cr.status === 'rejected' || cr.status === 'rolled-back')) {
      html += `<div class="change-timeline__rejection">Reason: ${escapeHtml(cr.rejectionReason)}`;
      if (cr.linkedIncident) {
        html += ` | Linked Incident: <span class="change-timeline__incident-link">${escapeHtml(cr.linkedIncident)}</span>`;
      }
      html += '</div>';
    }

    html += '</div>';
  }

  html += '</div>';
  return html;
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

export {
  renderChangeTimeline,
  renderTimelineHTML,
};
