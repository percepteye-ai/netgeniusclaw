/**
 * a2ui-renderer.js — A2UI JSON envelope builder for Canvas visualizations.
 *
 * Builds the root A2UI output structure per the a2ui-output-contract.md.
 * Supports all 7 visualization component types plus error-card.
 * Each render call emits a GAIT audit log entry via gait-logger.js.
 */

import { logVisualizationEvent } from './gait-logger.js';

/**
 * Generate a UUID v4 string.
 * @returns {string}
 */
function generateId() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

// Registered component types
const COMPONENT_REGISTRY = new Map();

/**
 * Register a visualization component type.
 * @param {string} componentType - e.g. 'topology-map', 'dashboard-panel'
 * @param {object} config - { buildContent: function, defaultTitle: string }
 */
function registerComponent(componentType, config) {
  COMPONENT_REGISTRY.set(componentType, config);
}

/**
 * Build the A2UI JSON envelope for a visualization.
 * @param {object} options
 * @param {string} options.component - Component type name
 * @param {string} [options.title] - Override title
 * @param {Array} options.dataSources - DataSourceRef[]
 * @param {object} options.scope - Scope object
 * @param {Array} [options.warnings] - Warning[]
 * @param {object} options.content - Visualization-specific content
 * @returns {object} A2UI JSON envelope
 */
function buildA2UIEnvelope({ component, title, dataSources, scope, warnings, content }) {
  const startTime = Date.now();
  const registered = COMPONENT_REGISTRY.get(component);
  const resolvedTitle = title || (registered && registered.defaultTitle) || component;

  const envelope = {
    a2ui: {
      version: '1.0',
      type: 'canvas',
      component,
      props: {
        id: generateId(),
        title: resolvedTitle,
        timestamp: new Date().toISOString(),
        dataSources: dataSources || [],
        scope: scope || {},
        warnings: warnings || [],
        content: content || {},
      },
    },
  };

  const renderDuration = Date.now() - startTime;

  // Determine status from warnings and data sources
  const status = determineStatus(dataSources, content);

  // Emit GAIT log
  logVisualizationEvent({
    visualizationType: component,
    dataSources: (dataSources || []).map(ds => `${ds.server}:${ds.tool}`),
    scope: scope || {},
    status,
    renderDurationMs: renderDuration,
  });

  return envelope;
}

/**
 * Build an error-card A2UI envelope when visualization cannot be generated.
 * @param {object} options
 * @param {string} options.title - Error title
 * @param {string} options.message - Human-readable error explanation
 * @param {string} options.suggestion - What the operator can do instead
 * @returns {object} A2UI JSON error-card envelope
 */
function buildErrorCard({ title, message, suggestion }) {
  const envelope = {
    a2ui: {
      version: '1.0',
      type: 'canvas',
      component: 'error-card',
      props: {
        title: title || 'Visualization Unavailable',
        message: message || 'Unable to generate the requested visualization.',
        suggestion: suggestion || 'Check that the required data sources are configured and operational.',
        timestamp: new Date().toISOString(),
      },
    },
  };

  logVisualizationEvent({
    visualizationType: 'error-card',
    dataSources: [],
    scope: {},
    status: 'failed',
    renderDurationMs: 0,
  });

  return envelope;
}

/**
 * Determine the overall visualization status from data sources.
 * @param {Array} dataSources - DataSourceRef[]
 * @param {object} content - Visualization content
 * @returns {'complete'|'degraded'|'failed'}
 */
function determineStatus(dataSources, content) {
  if (!dataSources || dataSources.length === 0) return 'failed';

  const statuses = dataSources.map(ds => ds.status);
  if (statuses.every(s => s === 'unavailable')) return 'failed';
  if (statuses.some(s => s === 'unavailable' || s === 'partial')) return 'degraded';
  return 'complete';
}

/**
 * Create a DataSourceRef entry for tracking MCP tool invocations.
 * @param {object} options
 * @param {string} options.server - MCP server name
 * @param {string} options.tool - MCP tool name
 * @param {'ok'|'partial'|'unavailable'} options.status
 * @param {number} [options.latencyMs]
 * @returns {object} DataSourceRef
 */
function createDataSourceRef({ server, tool, status, latencyMs }) {
  return {
    server,
    tool,
    status: status || 'ok',
    fetchedAt: new Date().toISOString(),
    latencyMs: latencyMs || undefined,
  };
}

/**
 * Create a Warning entry.
 * @param {'info'|'warning'|'error'} level
 * @param {string} message
 * @param {string} [source]
 * @returns {object} Warning
 */
function createWarning(level, message, source) {
  return {
    level,
    message,
    source: source || undefined,
  };
}

// ── Register all 7 visualization component types ──

registerComponent('topology-map', {
  defaultTitle: 'Network Topology',
});

registerComponent('dashboard-panel', {
  defaultTitle: 'Health Dashboard',
});

registerComponent('alert-card', {
  defaultTitle: 'Active Alerts',
});

registerComponent('change-timeline', {
  defaultTitle: 'Change Request Timeline',
});

registerComponent('diff-view', {
  defaultTitle: 'Configuration Diff',
});

registerComponent('path-trace', {
  defaultTitle: 'Path Trace',
});

registerComponent('health-scorecard', {
  defaultTitle: 'Health Scorecard',
});

export {
  generateId,
  registerComponent,
  buildA2UIEnvelope,
  buildErrorCard,
  determineStatus,
  createDataSourceRef,
  createWarning,
  COMPONENT_REGISTRY,
};
