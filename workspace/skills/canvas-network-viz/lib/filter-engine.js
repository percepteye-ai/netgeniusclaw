/**
 * filter-engine.js — Scope filtering for Canvas visualizations.
 *
 * Supports filtering by device name, site, device role, severity level,
 * and time range. Used by all visualization components to narrow data
 * to the operator's requested scope.
 */

/**
 * @typedef {object} Scope
 * @property {string[]} [devices] - Device hostnames to include
 * @property {string[]} [sites] - Site names to include
 * @property {string[]} [roles] - Device roles to include (spine, leaf, router, etc.)
 * @property {string[]} [severities] - Severity levels to include (critical, warning, info)
 * @property {{ start: string, end: string }} [timeRange] - ISO 8601 time range
 */

/**
 * Check if a scope object has any active filters.
 * @param {Scope} scope
 * @returns {boolean}
 */
function hasActiveFilters(scope) {
  if (!scope) return false;
  if (scope.devices && scope.devices.length > 0) return true;
  if (scope.sites && scope.sites.length > 0) return true;
  if (scope.roles && scope.roles.length > 0) return true;
  if (scope.severities && scope.severities.length > 0) return true;
  if (scope.timeRange && scope.timeRange.start && scope.timeRange.end) return true;
  return false;
}

/**
 * Describe the active filters as a human-readable string.
 * @param {Scope} scope
 * @returns {string|null} Description or null if no filters active
 */
function describeFilters(scope) {
  if (!scope || !hasActiveFilters(scope)) return null;

  const parts = [];
  if (scope.devices && scope.devices.length > 0) {
    parts.push(`devices: ${scope.devices.join(', ')}`);
  }
  if (scope.sites && scope.sites.length > 0) {
    parts.push(`sites: ${scope.sites.join(', ')}`);
  }
  if (scope.roles && scope.roles.length > 0) {
    parts.push(`roles: ${scope.roles.join(', ')}`);
  }
  if (scope.severities && scope.severities.length > 0) {
    parts.push(`severity: ${scope.severities.join(', ')}`);
  }
  if (scope.timeRange) {
    parts.push(`time: ${scope.timeRange.start} to ${scope.timeRange.end}`);
  }
  return `Filtered by ${parts.join('; ')}`;
}

/**
 * Filter topology nodes by scope.
 * @param {Array<object>} nodes - TopologyNode[] with id, site, role properties
 * @param {Scope} scope
 * @returns {Array<object>} Filtered nodes
 */
function filterNodes(nodes, scope) {
  if (!scope || !hasActiveFilters(scope)) return nodes;
  if (!nodes) return [];

  return nodes.filter(node => {
    if (scope.devices && scope.devices.length > 0) {
      const match = scope.devices.some(d =>
        node.id.toLowerCase().includes(d.toLowerCase()) ||
        (node.label && node.label.toLowerCase().includes(d.toLowerCase()))
      );
      if (!match) return false;
    }
    if (scope.sites && scope.sites.length > 0) {
      if (!node.site) return false;
      const match = scope.sites.some(s =>
        node.site.toLowerCase() === s.toLowerCase()
      );
      if (!match) return false;
    }
    if (scope.roles && scope.roles.length > 0) {
      if (!node.role) return false;
      const match = scope.roles.some(r =>
        node.role.toLowerCase() === r.toLowerCase()
      );
      if (!match) return false;
    }
    return true;
  });
}

/**
 * Filter edges to only include those where both source and target
 * are in the filtered node set.
 * @param {Array<object>} edges - TopologyEdge[] with source, target properties
 * @param {Array<object>} filteredNodes - Already-filtered TopologyNode[]
 * @returns {Array<object>} Filtered edges
 */
function filterEdges(edges, filteredNodes) {
  if (!edges || !filteredNodes) return [];
  const nodeIds = new Set(filteredNodes.map(n => n.id));
  return edges.filter(e => nodeIds.has(e.source) && nodeIds.has(e.target));
}

/**
 * Filter alerts by scope (severity, device, time range).
 * @param {Array<object>} alerts - AlertCard[] with severity, device, triggeredAt
 * @param {Scope} scope
 * @returns {Array<object>} Filtered alerts
 */
function filterAlerts(alerts, scope) {
  if (!scope || !hasActiveFilters(scope)) return alerts;
  if (!alerts) return [];

  return alerts.filter(alert => {
    if (scope.severities && scope.severities.length > 0) {
      if (!scope.severities.includes(alert.severity)) return false;
    }
    if (scope.devices && scope.devices.length > 0) {
      if (!alert.device) return false;
      const match = scope.devices.some(d =>
        alert.device.toLowerCase().includes(d.toLowerCase())
      );
      if (!match) return false;
    }
    if (scope.timeRange && scope.timeRange.start && scope.timeRange.end) {
      const alertTime = new Date(alert.triggeredAt).getTime();
      const start = new Date(scope.timeRange.start).getTime();
      const end = new Date(scope.timeRange.end).getTime();
      if (alertTime < start || alertTime > end) return false;
    }
    return true;
  });
}

/**
 * Filter change requests by scope (time range).
 * @param {Array<object>} changeRequests - ChangeRequestTimeline[]
 * @param {Scope} scope
 * @returns {Array<object>} Filtered change requests
 */
function filterChangeRequests(changeRequests, scope) {
  if (!scope || !hasActiveFilters(scope)) return changeRequests;
  if (!changeRequests) return [];

  return changeRequests.filter(cr => {
    if (scope.timeRange && cr.scheduledWindow) {
      const windowStart = new Date(cr.scheduledWindow.start).getTime();
      const windowEnd = new Date(cr.scheduledWindow.end).getTime();
      const filterStart = new Date(scope.timeRange.start).getTime();
      const filterEnd = new Date(scope.timeRange.end).getTime();
      // Include CR if its window overlaps with the filter range
      if (windowEnd < filterStart || windowStart > filterEnd) return false;
    }
    return true;
  });
}

/**
 * Filter dashboard panels by device scope.
 * @param {Array<object>} panels - DashboardPanel[]
 * @param {Scope} scope
 * @returns {Array<object>} Filtered panels
 */
function filterPanels(panels, scope) {
  // Dashboard panels are typically already device-scoped at fetch time.
  // This filter is a pass-through unless panels have device metadata.
  if (!panels) return [];
  return panels;
}

/**
 * Parse a natural language filter request into a Scope object.
 * Examples:
 *   "show topology for Site-A" -> { sites: ["Site-A"] }
 *   "show critical alerts only" -> { severities: ["critical"] }
 *   "show alerts for R2" -> { devices: ["R2"] }
 *   "show spine topology" -> { roles: ["spine"] }
 * @param {string} request - Natural language request
 * @returns {Scope}
 */
function parseFilterFromRequest(request) {
  const scope = {};
  if (!request) return scope;
  const lower = request.toLowerCase();

  // Site filter: "for Site-X" or "for site X"
  const siteMatch = request.match(/for\s+(?:site[- ]?)(\S+)/i);
  if (siteMatch) {
    scope.sites = [siteMatch[1]];
  }

  // Device filter: "for R1" or "for device R1"
  const deviceMatch = request.match(/for\s+(?:device\s+)?([A-Za-z0-9][\w.-]+)/i);
  if (deviceMatch && !siteMatch) {
    scope.devices = [deviceMatch[1]];
  }

  // Role filter: "spine topology", "leaf devices"
  const roles = ['spine', 'leaf', 'router', 'switch', 'firewall', 'border', 'core', 'access', 'distribution'];
  for (const role of roles) {
    if (lower.includes(role)) {
      scope.roles = scope.roles || [];
      scope.roles.push(role);
    }
  }

  // Severity filter: "critical alerts", "warning only"
  const severities = ['critical', 'warning', 'info'];
  for (const sev of severities) {
    if (lower.includes(sev)) {
      scope.severities = scope.severities || [];
      scope.severities.push(sev);
    }
  }

  return scope;
}

export {
  hasActiveFilters,
  describeFilters,
  filterNodes,
  filterEdges,
  filterAlerts,
  filterChangeRequests,
  filterPanels,
  parseFilterFromRequest,
};
