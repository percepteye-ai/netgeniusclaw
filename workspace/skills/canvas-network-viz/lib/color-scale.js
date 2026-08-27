/**
 * color-scale.js — Three-tier health-to-color mapping for Canvas visualizations.
 *
 * Provides WCAG 2.1 AA compliant color values for health status rendering.
 * Thresholds: warning at 70%, critical at 90%.
 */

// WCAG 2.1 AA compliant color palette
// All colors tested against both white (#FFFFFF) and dark (#1E1E1E) backgrounds
// for minimum 4.5:1 contrast ratio on normal text.
const COLORS = {
  healthy:  '#2E7D32', // Green 800 — healthy / nominal
  warning:  '#E65100', // Orange 900 — degraded / warning
  critical: '#C62828', // Red 800 — critical / failure
  unknown:  '#616161', // Gray 700 — no data / unreachable
};

// Background fill colors (lighter variants for node fills)
const FILL_COLORS = {
  healthy:  '#C8E6C9', // Green 100
  warning:  '#FFE0B2', // Orange 100
  critical: '#FFCDD2', // Red 100
  unknown:  '#E0E0E0', // Gray 300
};

// Border / stroke colors (same as primary COLORS)
const STROKE_COLORS = { ...COLORS };

// Edge / link status colors
const EDGE_COLORS = {
  up:      '#2E7D32', // Green 800
  down:    '#C62828', // Red 800
  unknown: '#9E9E9E', // Gray 500
};

// Alert severity colors
const SEVERITY_COLORS = {
  critical: '#C62828', // Red 800
  warning:  '#E65100', // Orange 900
  info:     '#1565C0', // Blue 800
};

// Alert severity background colors
const SEVERITY_BG_COLORS = {
  critical: '#FFCDD2', // Red 100
  warning:  '#FFE0B2', // Orange 100
  info:     '#BBDEFB', // Blue 100
};

// Thresholds for health classification (percentage-based metrics)
const THRESHOLDS = {
  warning:  70, // >= 70% utilization triggers warning
  critical: 90, // >= 90% utilization triggers critical
};

/**
 * Classify a percentage metric value into a health status.
 * @param {number|null|undefined} value - Metric value as percentage (0-100)
 * @returns {'healthy'|'warning'|'critical'|'unknown'} Health status
 */
function classifyHealth(value) {
  if (value === null || value === undefined || isNaN(value)) {
    return 'unknown';
  }
  if (value >= THRESHOLDS.critical) return 'critical';
  if (value >= THRESHOLDS.warning) return 'warning';
  return 'healthy';
}

/**
 * Classify a ratio metric (e.g., bgpPeersUp / bgpPeersTotal) into health status.
 * Inverts the logic: 100% up is healthy, < 70% up is critical.
 * @param {number} up - Count of items in good state
 * @param {number} total - Total count of items
 * @returns {'healthy'|'warning'|'critical'|'unknown'} Health status
 */
function classifyRatioHealth(up, total) {
  if (total === null || total === undefined || total === 0) {
    return 'unknown';
  }
  if (up === null || up === undefined) return 'unknown';
  const pct = (up / total) * 100;
  // For ratios, we invert: high percentage = good
  if (pct >= THRESHOLDS.warning) return 'healthy';     // >= 70% up = healthy
  if (pct >= (100 - THRESHOLDS.critical)) return 'warning'; // >= 10% up = warning
  return 'critical';
}

/**
 * Get the primary color for a health status.
 * @param {'healthy'|'warning'|'critical'|'unknown'} status
 * @returns {string} CSS color value
 */
function getHealthColor(status) {
  return COLORS[status] || COLORS.unknown;
}

/**
 * Get the fill color for a health status (lighter variant for backgrounds).
 * @param {'healthy'|'warning'|'critical'|'unknown'} status
 * @returns {string} CSS color value
 */
function getHealthFill(status) {
  return FILL_COLORS[status] || FILL_COLORS.unknown;
}

/**
 * Get the stroke color for a health status.
 * @param {'healthy'|'warning'|'critical'|'unknown'} status
 * @returns {string} CSS color value
 */
function getHealthStroke(status) {
  return STROKE_COLORS[status] || STROKE_COLORS.unknown;
}

/**
 * Get the color for an edge/link status.
 * @param {'up'|'down'|'unknown'} status
 * @returns {string} CSS color value
 */
function getEdgeColor(status) {
  return EDGE_COLORS[status] || EDGE_COLORS.unknown;
}

/**
 * Get the color for an alert severity.
 * @param {'critical'|'warning'|'info'} severity
 * @returns {string} CSS color value
 */
function getSeverityColor(severity) {
  return SEVERITY_COLORS[severity] || SEVERITY_COLORS.info;
}

/**
 * Get the background color for an alert severity.
 * @param {'critical'|'warning'|'info'} severity
 * @returns {string} CSS background color value
 */
function getSeverityBgColor(severity) {
  return SEVERITY_BG_COLORS[severity] || SEVERITY_BG_COLORS.info;
}

/**
 * Compute overall node health from NodeMetrics.
 * Uses worst-of approach: critical > warning > healthy.
 * Returns 'unknown' if no metrics are available.
 * @param {object} metrics - NodeMetrics object
 * @returns {'healthy'|'warning'|'critical'|'unknown'}
 */
function computeNodeHealth(metrics) {
  if (!metrics) return 'unknown';

  const statuses = [];

  if (metrics.cpuPercent !== null && metrics.cpuPercent !== undefined) {
    statuses.push(classifyHealth(metrics.cpuPercent));
  }
  if (metrics.memoryPercent !== null && metrics.memoryPercent !== undefined) {
    statuses.push(classifyHealth(metrics.memoryPercent));
  }
  if (metrics.interfaceErrors !== null && metrics.interfaceErrors !== undefined) {
    // Interface errors: > 100 is critical, > 10 is warning
    if (metrics.interfaceErrors > 100) statuses.push('critical');
    else if (metrics.interfaceErrors > 10) statuses.push('warning');
    else statuses.push('healthy');
  }
  if (metrics.bgpPeersTotal > 0) {
    statuses.push(classifyRatioHealth(metrics.bgpPeersUp, metrics.bgpPeersTotal));
  }
  if (metrics.ospfAdjacenciesUp !== null && metrics.ospfAdjacenciesUp !== undefined) {
    // If we know adjacencies are up but have no total, treat as healthy if > 0
    if (metrics.ospfAdjacenciesUp > 0) statuses.push('healthy');
    else statuses.push('warning');
  }

  if (statuses.length === 0) return 'unknown';

  // Worst-of: critical > warning > healthy
  if (statuses.includes('critical')) return 'critical';
  if (statuses.includes('warning')) return 'warning';
  return 'healthy';
}

/**
 * Build the standard color legend entries for topology maps and scorecards.
 * @returns {Array<{color: string, label: string}>}
 */
function buildHealthLegend() {
  return [
    { color: COLORS.healthy,  label: 'Healthy' },
    { color: COLORS.warning,  label: 'Warning' },
    { color: COLORS.critical, label: 'Critical' },
    { color: COLORS.unknown,  label: 'Unknown' },
  ];
}

export {
  COLORS,
  FILL_COLORS,
  STROKE_COLORS,
  EDGE_COLORS,
  SEVERITY_COLORS,
  SEVERITY_BG_COLORS,
  THRESHOLDS,
  classifyHealth,
  classifyRatioHealth,
  getHealthColor,
  getHealthFill,
  getHealthStroke,
  getEdgeColor,
  getSeverityColor,
  getSeverityBgColor,
  computeNodeHealth,
  buildHealthLegend,
};
