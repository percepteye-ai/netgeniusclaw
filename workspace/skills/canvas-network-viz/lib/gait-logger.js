/**
 * gait-logger.js — GAIT audit event emitter for visualization events.
 *
 * Emits GAIT log entries for each visualization generation event,
 * using the existing gait-session-tracking skill mechanism.
 * Each entry records: type, dataSources, scope, status, renderDurationMs, timestamp.
 */

/**
 * @typedef {object} VisualizationEvent
 * @property {string} visualizationType - Component type (topology-map, dashboard-panel, etc.)
 * @property {string[]} dataSources - List of "server:tool" strings
 * @property {object} scope - Scope object { devices, sites, roles, severities, timeRange }
 * @property {'complete'|'degraded'|'failed'} status - Visualization status
 * @property {number} renderDurationMs - Time to render in milliseconds
 */

// In-memory log buffer for the current session.
// The GAIT MCP server (gait_record_turn) is called by the agent after
// the visualization is returned. This buffer allows batch retrieval
// of events for the session summary.
const SESSION_LOG = [];

/**
 * Log a visualization generation event.
 * Creates the GAIT audit entry and stores it in the session buffer.
 * The OpenClaw agent is expected to call gait_record_turn with this
 * data as part of its normal session lifecycle.
 *
 * @param {VisualizationEvent} event
 * @returns {object} The GAIT log entry
 */
function logVisualizationEvent(event) {
  const entry = {
    event: 'visualization_generated',
    visualizationType: event.visualizationType || 'unknown',
    dataSources: event.dataSources || [],
    scope: event.scope || {},
    status: event.status || 'complete',
    renderDurationMs: event.renderDurationMs || 0,
    timestamp: new Date().toISOString(),
  };

  SESSION_LOG.push(entry);

  // Log to console for observability during development
  const sourceList = entry.dataSources.length > 0
    ? entry.dataSources.join(', ')
    : 'none';
  console.log(
    `[GAIT] visualization_generated | type=${entry.visualizationType} ` +
    `| status=${entry.status} | sources=${sourceList} ` +
    `| duration=${entry.renderDurationMs}ms`
  );

  return entry;
}

/**
 * Get all visualization events logged in the current session.
 * @returns {Array<object>} Array of GAIT log entries
 */
function getSessionLog() {
  return [...SESSION_LOG];
}

/**
 * Clear the session log buffer (e.g., at session end after gait_log).
 */
function clearSessionLog() {
  SESSION_LOG.length = 0;
}

/**
 * Get a summary of the session's visualization events for GAIT recording.
 * Suitable for passing to gait_record_turn as the response field.
 * @returns {string} Human-readable summary
 */
function getSessionSummary() {
  if (SESSION_LOG.length === 0) {
    return 'No visualizations generated in this session.';
  }

  const counts = {};
  let totalDuration = 0;
  let failedCount = 0;
  let degradedCount = 0;

  for (const entry of SESSION_LOG) {
    counts[entry.visualizationType] = (counts[entry.visualizationType] || 0) + 1;
    totalDuration += entry.renderDurationMs;
    if (entry.status === 'failed') failedCount++;
    if (entry.status === 'degraded') degradedCount++;
  }

  const typeSummary = Object.entries(counts)
    .map(([type, count]) => `${type}: ${count}`)
    .join(', ');

  let summary = `Generated ${SESSION_LOG.length} visualization(s): ${typeSummary}. `;
  summary += `Total render time: ${totalDuration}ms. `;
  if (failedCount > 0) summary += `Failed: ${failedCount}. `;
  if (degradedCount > 0) summary += `Degraded: ${degradedCount}. `;

  return summary;
}

/**
 * Build a GAIT turn payload for the visualization skill session.
 * This is the format expected by gait_record_turn.
 * @param {string} prompt - What was requested
 * @param {string} visualizationType - What type was generated
 * @param {'complete'|'degraded'|'failed'} status - Result status
 * @returns {object} { prompt, response, artifacts }
 */
function buildGaitTurnPayload(prompt, visualizationType, status) {
  return {
    prompt: prompt || `Generate ${visualizationType} visualization`,
    response: `Generated ${visualizationType} visualization. Status: ${status}. ${getSessionSummary()}`,
    artifacts: [],
  };
}

export {
  logVisualizationEvent,
  getSessionLog,
  clearSessionLog,
  getSessionSummary,
  buildGaitTurnPayload,
};
