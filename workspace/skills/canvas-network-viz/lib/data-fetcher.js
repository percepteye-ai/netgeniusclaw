/**
 * data-fetcher.js — MCP tool invocation abstraction for Canvas visualizations.
 *
 * Provides data fetching pipelines for all 7 visualization types.
 * Supports pyATS, Grafana, Prometheus, ServiceNow, SuzieQ, and Batfish MCP servers.
 * Includes per-source status tracking (ok/partial/unavailable) and latency measurement.
 */

import { createDataSourceRef, createWarning } from './a2ui-renderer.js';
import { computeNodeHealth, classifyHealth } from './color-scale.js';

// ── MCP Tool Invocation ──────────────────────────────────────────────

/**
 * Invoke an MCP tool and track its status/latency.
 * In production, this calls through the OpenClaw MCP framework.
 * @param {string} server - MCP server name (pyats, grafana, prometheus, etc.)
 * @param {string} tool - Tool name (pyats_show_cdp_neighbors, etc.)
 * @param {object} params - Tool parameters
 * @returns {Promise<{ data: any, ref: object }>} Data and DataSourceRef
 */
async function invokeMcpTool(server, tool, params) {
  const startTime = Date.now();
  try {
    // The OpenClaw agent runtime provides mcp_call or equivalent.
    // In skill context, we use the global mcp tool invocation mechanism.
    // This abstraction allows the visualization to be generated regardless
    // of the specific MCP call mechanism.
    let data = null;

    if (typeof globalThis.mcp_call === 'function') {
      data = await globalThis.mcp_call(server, tool, params);
    } else if (typeof globalThis.mcpInvoke === 'function') {
      data = await globalThis.mcpInvoke({ server, tool, params });
    } else {
      // Fallback: return null data with unavailable status
      const latency = Date.now() - startTime;
      return {
        data: null,
        ref: createDataSourceRef({ server, tool, status: 'unavailable', latencyMs: latency }),
      };
    }

    const latency = Date.now() - startTime;
    return {
      data,
      ref: createDataSourceRef({ server, tool, status: 'ok', latencyMs: latency }),
    };
  } catch (err) {
    const latency = Date.now() - startTime;
    console.error(`[data-fetcher] ${server}:${tool} failed:`, err.message || err);
    return {
      data: null,
      ref: createDataSourceRef({ server, tool, status: 'unavailable', latencyMs: latency }),
    };
  }
}

// ── Topology Data Pipeline (US1, T011) ───────────────────────────────

/**
 * Fetch topology data: CDP/LLDP neighbors + health metrics.
 * Transforms into TopologyNode[] and TopologyEdge[].
 * @param {object} [scope] - Optional scope for filtering
 * @returns {Promise<{ nodes: Array, edges: Array, dataSources: Array, warnings: Array }>}
 */
async function fetchTopologyData(scope) {
  const dataSources = [];
  const warnings = [];
  let nodes = [];
  let edges = [];
  const nodeMap = new Map();

  // Fetch CDP neighbors
  const cdpResult = await invokeMcpTool('pyats', 'pyats_show_cdp_neighbors', {});
  dataSources.push(cdpResult.ref);

  // Fetch LLDP neighbors
  const lldpResult = await invokeMcpTool('pyats', 'pyats_show_lldp_neighbors', {});
  dataSources.push(lldpResult.ref);

  // Process CDP data
  if (cdpResult.data) {
    processNeighborData(cdpResult.data, 'CDP', nodeMap, edges);
  }

  // Process LLDP data
  if (lldpResult.data) {
    processNeighborData(lldpResult.data, 'LLDP', nodeMap, edges);
  }

  if (nodeMap.size === 0) {
    return { nodes: [], edges: [], dataSources, warnings };
  }

  // Fetch health metrics for discovered nodes
  const healthResult = await fetchHealthMetricsForNodes([...nodeMap.keys()]);
  dataSources.push(...healthResult.dataSources);
  warnings.push(...healthResult.warnings);

  // Apply health metrics to nodes
  for (const [id, node] of nodeMap) {
    const metrics = healthResult.metrics.get(id) || null;
    node.metrics = metrics;
    node.health = computeNodeHealth(metrics);
    nodes.push(node);
  }

  return { nodes, edges, dataSources, warnings };
}

/**
 * Process neighbor data (CDP or LLDP) into nodes and edges.
 * @param {object} data - Raw neighbor data from MCP tool
 * @param {string} protocol - 'CDP' or 'LLDP'
 * @param {Map} nodeMap - Accumulator for nodes
 * @param {Array} edges - Accumulator for edges
 */
function processNeighborData(data, protocol, nodeMap, edges) {
  // Handle various MCP response formats
  const devices = data.devices || data.result || data;
  if (!devices || typeof devices !== 'object') return;

  for (const [deviceName, deviceData] of Object.entries(devices)) {
    // Ensure source device is in node map
    if (!nodeMap.has(deviceName)) {
      nodeMap.set(deviceName, {
        id: deviceName,
        label: deviceName,
        role: inferDeviceRole(deviceName),
        site: null,
        health: 'unknown',
        metrics: null,
        x: null,
        y: null,
      });
    }

    // Process neighbors
    const neighbors = deviceData.neighbors || deviceData.interfaces || deviceData;
    if (!neighbors || typeof neighbors !== 'object') continue;

    for (const [intf, intfData] of Object.entries(neighbors)) {
      const neighborEntries = Array.isArray(intfData) ? intfData : [intfData];
      for (const neighbor of neighborEntries) {
        const neighborName = neighbor.device_id || neighbor.system_name ||
                            neighbor.neighbor || neighbor.chassis_id || 'unknown';
        const neighborIntf = neighbor.port_id || neighbor.port || neighbor.interface || '';

        // Add neighbor as node
        if (!nodeMap.has(neighborName)) {
          nodeMap.set(neighborName, {
            id: neighborName,
            label: neighborName,
            role: inferDeviceRole(neighborName),
            site: null,
            health: 'unknown',
            metrics: null,
            x: null,
            y: null,
          });
        }

        // Add edge (deduplicate by checking reverse)
        const edgeExists = edges.some(e =>
          (e.source === deviceName && e.target === neighborName && e.sourceInterface === intf) ||
          (e.source === neighborName && e.target === deviceName && e.targetInterface === intf)
        );

        if (!edgeExists) {
          edges.push({
            source: deviceName,
            target: neighborName,
            sourceInterface: intf,
            targetInterface: neighborIntf,
            protocol,
            status: 'up',
          });
        }
      }
    }
  }
}

/**
 * Infer device role from hostname patterns.
 * @param {string} hostname
 * @returns {string|null}
 */
function inferDeviceRole(hostname) {
  if (!hostname) return null;
  const lower = hostname.toLowerCase();
  if (lower.includes('spine') || lower.includes('spn')) return 'spine';
  if (lower.includes('leaf') || lower.includes('lf')) return 'leaf';
  if (lower.includes('border') || lower.includes('bdr')) return 'border';
  if (lower.includes('core') || lower.includes('cr')) return 'core';
  if (lower.includes('dist') || lower.includes('dr')) return 'distribution';
  if (lower.includes('access') || lower.includes('as')) return 'access';
  if (lower.match(/^fw|firewall|asa|ftd/)) return 'firewall';
  if (lower.match(/^sw|switch/)) return 'switch';
  if (lower.match(/^r\d|router|rtr/)) return 'router';
  return null;
}

/**
 * Fetch health metrics for a list of device hostnames.
 * Queries pyATS, Grafana, and Prometheus for CPU, memory, interface, BGP, OSPF data.
 * @param {string[]} deviceNames
 * @returns {Promise<{ metrics: Map, dataSources: Array, warnings: Array }>}
 */
async function fetchHealthMetricsForNodes(deviceNames) {
  const metrics = new Map();
  const dataSources = [];
  const warnings = [];

  // Try pyATS for health data
  const pyatsHealth = await invokeMcpTool('pyats', 'pyats_show_processes_cpu', {});
  dataSources.push(pyatsHealth.ref);

  const pyatsMemory = await invokeMcpTool('pyats', 'pyats_show_processes_memory', {});
  dataSources.push(pyatsMemory.ref);

  const pyatsBgp = await invokeMcpTool('pyats', 'pyats_show_bgp_summary', {});
  dataSources.push(pyatsBgp.ref);

  const pyatsOspf = await invokeMcpTool('pyats', 'pyats_show_ospf_neighbors', {});
  dataSources.push(pyatsOspf.ref);

  const pyatsInterfaces = await invokeMcpTool('pyats', 'pyats_show_interfaces', {});
  dataSources.push(pyatsInterfaces.ref);

  // Process metrics into per-device NodeMetrics
  for (const name of deviceNames) {
    const nodeMetrics = {
      cpuPercent: null,
      memoryPercent: null,
      interfaceErrors: null,
      bgpPeersUp: null,
      bgpPeersTotal: null,
      ospfAdjacenciesUp: null,
    };

    // Extract CPU from pyATS response
    if (pyatsHealth.data) {
      const cpuData = extractDeviceMetric(pyatsHealth.data, name, 'cpu');
      if (cpuData !== null) nodeMetrics.cpuPercent = cpuData;
    }

    // Extract memory from pyATS response
    if (pyatsMemory.data) {
      const memData = extractDeviceMetric(pyatsMemory.data, name, 'memory');
      if (memData !== null) nodeMetrics.memoryPercent = memData;
    }

    // Extract BGP peer counts
    if (pyatsBgp.data) {
      const bgpData = extractBgpMetrics(pyatsBgp.data, name);
      if (bgpData) {
        nodeMetrics.bgpPeersUp = bgpData.up;
        nodeMetrics.bgpPeersTotal = bgpData.total;
      }
    }

    // Extract OSPF adjacency counts
    if (pyatsOspf.data) {
      const ospfData = extractOspfMetrics(pyatsOspf.data, name);
      if (ospfData !== null) nodeMetrics.ospfAdjacenciesUp = ospfData;
    }

    // Extract interface error counts
    if (pyatsInterfaces.data) {
      const errCount = extractInterfaceErrors(pyatsInterfaces.data, name);
      if (errCount !== null) nodeMetrics.interfaceErrors = errCount;
    }

    metrics.set(name, nodeMetrics);
  }

  // Try Grafana/Prometheus as supplementary sources
  const grafanaResult = await invokeMcpTool('grafana', 'grafana_query_prometheus', {
    expr: 'device_cpu_utilization',
  });
  dataSources.push(grafanaResult.ref);

  if (grafanaResult.ref.status === 'unavailable') {
    warnings.push(createWarning('warning', 'Grafana metrics unavailable; using pyATS data only', 'grafana'));
  }

  const promResult = await invokeMcpTool('prometheus', 'prometheus_instant_query', {
    query: 'device_cpu_utilization',
  });
  dataSources.push(promResult.ref);

  if (promResult.ref.status === 'unavailable') {
    warnings.push(createWarning('warning', 'Prometheus metrics unavailable; using pyATS data only', 'prometheus'));
  }

  // Supplement metrics from Grafana/Prometheus if available
  if (grafanaResult.data || promResult.data) {
    supplementMetricsFromTimeSeries(metrics, grafanaResult.data || promResult.data, deviceNames);
  }

  return { metrics, dataSources, warnings };
}

/**
 * Extract a device-specific metric from pyATS response data.
 * @param {object} data - pyATS tool response
 * @param {string} device - Device hostname
 * @param {string} metricType - 'cpu' or 'memory'
 * @returns {number|null}
 */
function extractDeviceMetric(data, device, metricType) {
  const deviceData = data[device] || data.devices?.[device] || null;
  if (!deviceData) return null;

  if (metricType === 'cpu') {
    return deviceData.five_min_cpu || deviceData.cpu_utilization ||
           deviceData['5min_cpu'] || null;
  }
  if (metricType === 'memory') {
    if (deviceData.memory_used && deviceData.memory_total) {
      return Math.round((deviceData.memory_used / deviceData.memory_total) * 100);
    }
    return deviceData.memory_utilization || deviceData.memory_percent || null;
  }
  return null;
}

/**
 * Extract BGP peer metrics from pyATS BGP summary data.
 * @param {object} data
 * @param {string} device
 * @returns {{ up: number, total: number }|null}
 */
function extractBgpMetrics(data, device) {
  const deviceData = data[device] || data.devices?.[device] || null;
  if (!deviceData) return null;

  const peers = deviceData.peers || deviceData.neighbors || {};
  let up = 0;
  let total = 0;

  for (const [, peerData] of Object.entries(peers)) {
    total++;
    const state = peerData.state || peerData.session_state || '';
    if (state.toLowerCase() === 'established') up++;
  }

  return total > 0 ? { up, total } : null;
}

/**
 * Extract OSPF adjacency count from pyATS OSPF neighbor data.
 * @param {object} data
 * @param {string} device
 * @returns {number|null}
 */
function extractOspfMetrics(data, device) {
  const deviceData = data[device] || data.devices?.[device] || null;
  if (!deviceData) return null;

  const neighbors = deviceData.neighbors || deviceData.adjacencies || {};
  let fullCount = 0;

  for (const [, nbr] of Object.entries(neighbors)) {
    const state = nbr.state || nbr.adjacency_state || '';
    if (state.toLowerCase().includes('full')) fullCount++;
  }

  return fullCount;
}

/**
 * Extract total interface error count from pyATS interface data.
 * @param {object} data
 * @param {string} device
 * @returns {number|null}
 */
function extractInterfaceErrors(data, device) {
  const deviceData = data[device] || data.devices?.[device] || null;
  if (!deviceData) return null;

  let totalErrors = 0;
  const interfaces = deviceData.interfaces || deviceData;

  for (const [, intfData] of Object.entries(interfaces)) {
    totalErrors += (intfData.in_errors || 0) + (intfData.out_errors || 0) +
                   (intfData.in_crc_errors || 0) + (intfData.input_errors || 0) +
                   (intfData.output_errors || 0);
  }

  return totalErrors;
}

/**
 * Supplement node metrics from Prometheus/Grafana time series data.
 * @param {Map} metrics - Device -> NodeMetrics map
 * @param {object} tsData - Time series response
 * @param {string[]} deviceNames
 */
function supplementMetricsFromTimeSeries(metrics, tsData, deviceNames) {
  if (!tsData || !tsData.result) return;

  for (const series of tsData.result) {
    const device = series.metric?.device || series.metric?.instance || null;
    if (!device) continue;

    const matchedName = deviceNames.find(n =>
      n.toLowerCase() === device.toLowerCase() ||
      device.toLowerCase().includes(n.toLowerCase())
    );

    if (matchedName && metrics.has(matchedName)) {
      const nodeMetrics = metrics.get(matchedName);
      const value = parseFloat(series.value?.[1] || series.values?.[0]?.[1] || 0);
      const metricName = series.metric?.__name__ || '';

      if (metricName.includes('cpu') && nodeMetrics.cpuPercent === null) {
        nodeMetrics.cpuPercent = value;
      }
      if (metricName.includes('memory') && nodeMetrics.memoryPercent === null) {
        nodeMetrics.memoryPercent = value;
      }
    }
  }
}

// ── Dashboard Data Pipeline (US2, T019) ──────────────────────────────

/**
 * Fetch dashboard data for a device or site.
 * @param {string} target - Device hostname or site name
 * @param {boolean} [isSite=false] - If true, fetch site-level aggregated data
 * @returns {Promise<{ panels: Array, deviceSummary: string, dataSources: Array, warnings: Array }>}
 */
async function fetchDashboardData(target, isSite = false) {
  const dataSources = [];
  const warnings = [];
  const panels = [];

  // Fetch CPU metrics
  const cpuResult = await invokeMcpTool('pyats', 'pyats_show_processes_cpu',
    isSite ? {} : { device: target });
  dataSources.push(cpuResult.ref);

  // Fetch memory metrics
  const memResult = await invokeMcpTool('pyats', 'pyats_show_processes_memory',
    isSite ? {} : { device: target });
  dataSources.push(memResult.ref);

  // Fetch interface status
  const intfResult = await invokeMcpTool('pyats', 'pyats_show_interfaces',
    isSite ? {} : { device: target });
  dataSources.push(intfResult.ref);

  // Fetch BGP summary
  const bgpResult = await invokeMcpTool('pyats', 'pyats_show_bgp_summary',
    isSite ? {} : { device: target });
  dataSources.push(bgpResult.ref);

  // Fetch OSPF neighbors
  const ospfResult = await invokeMcpTool('pyats', 'pyats_show_ospf_neighbors',
    isSite ? {} : { device: target });
  dataSources.push(ospfResult.ref);

  // Try Grafana for richer metrics
  const grafanaResult = await invokeMcpTool('grafana', 'grafana_query_prometheus', {
    expr: `device_cpu_utilization{device="${target}"}`,
  });
  dataSources.push(grafanaResult.ref);

  if (grafanaResult.ref.status === 'unavailable') {
    warnings.push(createWarning('warning',
      'Grafana metrics unavailable; dashboard shows pyATS data only', 'grafana'));
  }

  // Try Prometheus direct
  const promResult = await invokeMcpTool('prometheus', 'prometheus_instant_query', {
    query: `device_cpu_utilization{device="${target}"}`,
  });
  dataSources.push(promResult.ref);

  if (promResult.ref.status === 'unavailable') {
    warnings.push(createWarning('warning',
      'Prometheus metrics unavailable; dashboard shows pyATS data only', 'prometheus'));
  }

  // Build CPU panel
  const cpuValue = cpuResult.data
    ? extractDeviceMetric(cpuResult.data, target, 'cpu')
    : null;
  if (cpuValue !== null) {
    panels.push({
      id: 'cpu',
      title: 'CPU Utilization',
      type: 'gauge',
      value: cpuValue,
      unit: '%',
      threshold: { warning: 70, critical: 90 },
    });
  }

  // Build memory panel
  const memValue = memResult.data
    ? extractDeviceMetric(memResult.data, target, 'memory')
    : null;
  if (memValue !== null) {
    panels.push({
      id: 'memory',
      title: 'Memory Utilization',
      type: 'gauge',
      value: memValue,
      unit: '%',
      threshold: { warning: 70, critical: 90 },
    });
  }

  // Build interface status panel
  if (intfResult.data) {
    const intfItems = buildInterfaceStatusItems(intfResult.data, target);
    if (intfItems.length > 0) {
      const upCount = intfItems.filter(i => i.status === 'up').length;
      panels.push({
        id: 'interfaces',
        title: 'Interface Status',
        type: 'status-list',
        value: `${upCount}/${intfItems.length} up`,
        items: intfItems,
      });
    }
  }

  // Build BGP peers panel
  if (bgpResult.data) {
    const bgpMetrics = extractBgpMetrics(bgpResult.data, target);
    if (bgpMetrics) {
      const bgpItems = buildBgpStatusItems(bgpResult.data, target);
      panels.push({
        id: 'bgp',
        title: 'BGP Peers',
        type: 'status-list',
        value: `${bgpMetrics.up}/${bgpMetrics.total} established`,
        items: bgpItems,
      });
    }
  }

  // Build OSPF adjacencies panel
  if (ospfResult.data) {
    const ospfCount = extractOspfMetrics(ospfResult.data, target);
    if (ospfCount !== null) {
      const ospfItems = buildOspfStatusItems(ospfResult.data, target);
      panels.push({
        id: 'ospf',
        title: 'OSPF Adjacencies',
        type: 'status-list',
        value: `${ospfCount} full`,
        items: ospfItems,
      });
    }
  }

  const deviceSummary = isSite
    ? `Site dashboard: ${target}`
    : `Device dashboard: ${target}`;

  return { panels, deviceSummary, dataSources, warnings };
}

/**
 * Build interface status items from pyATS interface data.
 */
function buildInterfaceStatusItems(data, device) {
  const deviceData = data[device] || data.devices?.[device] || data;
  const items = [];

  for (const [name, intfData] of Object.entries(deviceData.interfaces || deviceData)) {
    if (typeof intfData !== 'object') continue;
    const opStatus = intfData.oper_status || intfData.operational_status || intfData.status || 'unknown';
    items.push({
      name,
      status: opStatus.toLowerCase() === 'up' ? 'up' : opStatus.toLowerCase() === 'down' ? 'down' : 'unknown',
      detail: intfData.description || '',
    });
  }

  return items;
}

/**
 * Build BGP peer status items from pyATS BGP summary data.
 */
function buildBgpStatusItems(data, device) {
  const deviceData = data[device] || data.devices?.[device] || {};
  const peers = deviceData.peers || deviceData.neighbors || {};
  const items = [];

  for (const [peerIp, peerData] of Object.entries(peers)) {
    const state = (peerData.state || peerData.session_state || 'unknown').toLowerCase();
    items.push({
      name: peerIp,
      status: state === 'established' ? 'up' : 'down',
      detail: `AS ${peerData.remote_as || peerData.as || '?'}`,
    });
  }

  return items;
}

/**
 * Build OSPF neighbor status items from pyATS OSPF data.
 */
function buildOspfStatusItems(data, device) {
  const deviceData = data[device] || data.devices?.[device] || {};
  const neighbors = deviceData.neighbors || deviceData.adjacencies || {};
  const items = [];

  for (const [nbrId, nbrData] of Object.entries(neighbors)) {
    const state = (nbrData.state || nbrData.adjacency_state || 'unknown').toLowerCase();
    items.push({
      name: nbrId,
      status: state.includes('full') ? 'up' : state.includes('init') ? 'warning' : 'down',
      detail: `Area ${nbrData.area || '?'}`,
    });
  }

  return items;
}

// ── Alert Data Pipeline (US3, T025) ──────────────────────────────────

/**
 * Fetch active alerts from Grafana, Prometheus, and pyATS syslog.
 * @returns {Promise<{ alerts: Array, dataSources: Array, warnings: Array }>}
 */
async function fetchAlertData() {
  const dataSources = [];
  const warnings = [];
  const alerts = [];

  // Grafana alerts
  const grafanaAlerts = await invokeMcpTool('grafana', 'grafana_list_alerts', {});
  dataSources.push(grafanaAlerts.ref);

  if (grafanaAlerts.data) {
    const grafanaCards = processGrafanaAlerts(grafanaAlerts.data);
    alerts.push(...grafanaCards);
  }

  // Prometheus alertmanager alerts
  const promAlerts = await invokeMcpTool('prometheus', 'prometheus_alerts', {});
  dataSources.push(promAlerts.ref);

  if (promAlerts.data) {
    const promCards = processPrometheusAlerts(promAlerts.data);
    alerts.push(...promCards);
  }

  // pyATS syslog (best effort)
  const syslogResult = await invokeMcpTool('pyats', 'pyats_show_logging', {});
  dataSources.push(syslogResult.ref);

  if (syslogResult.data) {
    const syslogCards = processSyslogAlerts(syslogResult.data);
    alerts.push(...syslogCards);
  }

  // Sort by severity: critical first, then warning, then info
  const severityOrder = { critical: 0, warning: 1, info: 2 };
  alerts.sort((a, b) => (severityOrder[a.severity] || 3) - (severityOrder[b.severity] || 3));

  return { alerts, dataSources, warnings };
}

/**
 * Process Grafana alerts into AlertCard[].
 * Grafana severity mapping: alerting -> critical, pending -> warning
 */
function processGrafanaAlerts(data) {
  const alerts = data.alerts || data.results || (Array.isArray(data) ? data : []);
  return alerts.map((alert, i) => {
    const state = (alert.state || alert.status || '').toLowerCase();
    let severity = 'info';
    if (state === 'alerting' || state === 'firing') severity = 'critical';
    else if (state === 'pending') severity = 'warning';

    return {
      id: alert.id || alert.uid || `grafana-${i}`,
      name: alert.name || alert.title || alert.labels?.alertname || 'Unknown Alert',
      severity,
      source: 'Grafana',
      device: alert.labels?.device || alert.labels?.instance || null,
      interface: alert.labels?.interface || null,
      description: alert.annotations?.description || alert.annotations?.summary || alert.message || '',
      triggeredAt: alert.activeAt || alert.startsAt || new Date().toISOString(),
    };
  });
}

/**
 * Process Prometheus alerts into AlertCard[].
 * Prometheus severity mapping: critical -> critical, warning -> warning
 */
function processPrometheusAlerts(data) {
  const alerts = data.alerts || data.data?.alerts || (Array.isArray(data) ? data : []);
  return alerts.map((alert, i) => {
    const severity = alert.labels?.severity || 'info';
    return {
      id: alert.fingerprint || `prom-${i}`,
      name: alert.labels?.alertname || 'Unknown Alert',
      severity: ['critical', 'warning'].includes(severity) ? severity : 'info',
      source: 'Prometheus',
      device: alert.labels?.device || alert.labels?.instance || null,
      interface: alert.labels?.interface || null,
      description: alert.annotations?.description || alert.annotations?.summary || '',
      triggeredAt: alert.activeAt || alert.startsAt || new Date().toISOString(),
    };
  });
}

/**
 * Process syslog data into AlertCard[].
 * Syslog severity mapping: 0-2 -> critical, 3-4 -> warning, 5-7 -> info
 */
function processSyslogAlerts(data) {
  const alerts = [];
  const devices = data.devices || data;

  for (const [device, deviceData] of Object.entries(devices)) {
    const logs = deviceData.logs || deviceData.messages || [];
    if (!Array.isArray(logs)) continue;

    for (const log of logs.slice(-50)) { // Last 50 syslog entries
      const level = log.severity || log.level || 6;
      const numLevel = typeof level === 'number' ? level : parseInt(level, 10);
      let severity = 'info';
      if (numLevel <= 2) severity = 'critical';
      else if (numLevel <= 4) severity = 'warning';

      if (severity !== 'info') { // Only surface warning+ in alert view
        alerts.push({
          id: `syslog-${device}-${alerts.length}`,
          name: log.facility || log.mnemonic || 'Syslog Event',
          severity,
          source: 'syslog',
          device,
          interface: null,
          description: log.message || log.text || '',
          triggeredAt: log.timestamp || new Date().toISOString(),
        });
      }
    }
  }

  return alerts;
}

// ── Change Management Data Pipeline (US4, T030) ─────────────────────

/**
 * Fetch change request data from ServiceNow.
 * @param {string} [crNumber] - Specific CR number, or null for all active CRs
 * @returns {Promise<{ changeRequests: Array, dataSources: Array, warnings: Array }>}
 */
async function fetchChangeData(crNumber) {
  const dataSources = [];
  const warnings = [];
  const changeRequests = [];

  let result;
  if (crNumber) {
    result = await invokeMcpTool('servicenow', 'servicenow_get_change_request', {
      number: crNumber,
    });
  } else {
    result = await invokeMcpTool('servicenow', 'servicenow_list_change_requests', {
      state: 'active',
    });
  }
  dataSources.push(result.ref);

  if (!result.data) {
    return { changeRequests, dataSources, warnings };
  }

  const records = Array.isArray(result.data)
    ? result.data
    : result.data.result
      ? (Array.isArray(result.data.result) ? result.data.result : [result.data.result])
      : [result.data];

  for (const cr of records) {
    const stages = buildCrStages(cr);
    const currentStage = stages.find(s => s.status === 'active')?.name || stages[stages.length - 1]?.name || 'unknown';
    const crStatus = determineCrStatus(cr, stages);

    changeRequests.push({
      crNumber: cr.number || cr.sys_id || 'Unknown',
      description: cr.short_description || cr.description || '',
      assignee: cr.assigned_to?.display_value || cr.assigned_to || null,
      scheduledWindow: cr.start_date && cr.end_date ? {
        start: cr.start_date,
        end: cr.end_date,
      } : null,
      stages,
      currentStage,
      status: crStatus,
      rejectionReason: cr.rejection_reason || cr.close_notes || null,
      linkedIncident: cr.linked_incident || null,
    });
  }

  return { changeRequests, dataSources, warnings };
}

/**
 * Build timeline stages from a ServiceNow CR record.
 */
function buildCrStages(cr) {
  const stageNames = ['assess', 'authorize', 'implement', 'review'];
  const crState = (cr.state || cr.phase || '').toLowerCase();

  return stageNames.map((name, idx) => {
    let status = 'pending';

    if (crState.includes('closed') || crState.includes('complete') || crState.includes('review')) {
      status = idx <= 3 ? 'completed' : 'pending';
      if (name === 'review' && (crState.includes('closed') || crState.includes('complete'))) {
        status = 'completed';
      }
    }

    if (crState.includes(name)) {
      status = 'active';
      // Mark previous stages as completed
    }

    // Handle rejection
    if (cr.approval === 'rejected' && name === 'authorize') {
      status = 'failed';
    }

    return {
      name,
      status,
      completedAt: status === 'completed' ? (cr[`${name}_completed`] || null) : null,
    };
  });
}

/**
 * Determine overall CR status.
 */
function determineCrStatus(cr, stages) {
  const state = (cr.state || '').toLowerCase();
  if (state.includes('cancel') || cr.approval === 'rejected') return 'rejected';
  if (state.includes('rollback') || state.includes('backed out')) return 'rolled-back';
  if (state.includes('closed') || state.includes('complete')) return 'completed';
  return 'in-progress';
}

// ── Path Trace Data Pipeline (US5, T038) ─────────────────────────────

/**
 * Fetch path trace data from source to destination IP.
 * @param {string} sourceIp
 * @param {string} destIp
 * @returns {Promise<{ pathTrace: object, dataSources: Array, warnings: Array }>}
 */
async function fetchPathTraceData(sourceIp, destIp) {
  const dataSources = [];
  const warnings = [];

  // Fetch routing tables from pyATS
  const routeResult = await invokeMcpTool('pyats', 'pyats_show_ip_route', {
    destination: destIp,
  });
  dataSources.push(routeResult.ref);

  // Try SuzieQ for additional path data
  const suzieqResult = await invokeMcpTool('suzieq', 'suzieq_path_trace', {
    source: sourceIp,
    destination: destIp,
  });
  dataSources.push(suzieqResult.ref);

  const paths = [];
  let blackHole = null;

  if (suzieqResult.data && suzieqResult.data.paths) {
    // SuzieQ provides structured path data
    for (const [idx, path] of suzieqResult.data.paths.entries()) {
      const hops = (path.hops || []).map((hop, order) => ({
        order: order + 1,
        device: hop.device || hop.hostname || 'unknown',
        ingressInterface: hop.iif || hop.ingress || '',
        egressInterface: hop.oif || hop.egress || '',
        nextHop: hop.nexthop || hop.next_hop || '',
        action: hop.action || 'forward',
      }));

      paths.push({
        id: `path-${idx + 1}`,
        hops,
        isEcmp: suzieqResult.data.paths.length > 1,
      });
    }

    if (suzieqResult.data.blackhole) {
      blackHole = {
        lastHop: suzieqResult.data.blackhole.device || 'unknown',
        lastInterface: suzieqResult.data.blackhole.interface || '',
        reason: suzieqResult.data.blackhole.reason || 'no route to destination',
      };
    }
  } else if (routeResult.data) {
    // Build path from routing table data (single path approximation)
    const pathResult = buildPathFromRoutes(routeResult.data, sourceIp, destIp);
    if (pathResult.path) paths.push(pathResult.path);
    if (pathResult.blackHole) blackHole = pathResult.blackHole;
    if (pathResult.warning) warnings.push(pathResult.warning);
  }

  const pathTrace = {
    source: sourceIp,
    destination: destIp,
    paths,
    blackHole,
  };

  return { pathTrace, dataSources, warnings };
}

/**
 * Build a path trace from routing table data (fallback when SuzieQ unavailable).
 */
function buildPathFromRoutes(data, sourceIp, destIp) {
  const hops = [];
  const devices = data.devices || data;
  let hopOrder = 1;

  for (const [device, deviceData] of Object.entries(devices)) {
    const routes = deviceData.routes || deviceData;
    if (!routes || typeof routes !== 'object') continue;

    // Find the matching route for the destination
    for (const [prefix, routeData] of Object.entries(routes)) {
      const nextHops = routeData.next_hop || routeData.nexthop || {};
      if (typeof nextHops === 'object') {
        for (const [nh, nhData] of Object.entries(nextHops)) {
          hops.push({
            order: hopOrder++,
            device,
            ingressInterface: nhData.incoming_interface || '',
            egressInterface: nhData.outgoing_interface || nhData.interface || '',
            nextHop: nh,
            action: routeData.source_protocol || 'longest-match',
          });
          break; // Take first next-hop for single path
        }
      }
    }
  }

  if (hops.length === 0) {
    return {
      path: null,
      blackHole: {
        lastHop: Object.keys(devices)[0] || 'unknown',
        lastInterface: '',
        reason: 'no route to destination',
      },
      warning: createWarning('warning',
        'Path built from routing tables only; SuzieQ unavailable for complete trace', 'suzieq'),
    };
  }

  return {
    path: { id: 'path-1', hops, isEcmp: false },
    blackHole: null,
    warning: createWarning('info',
      'Path built from routing tables; SuzieQ unavailable for ECMP detection', 'suzieq'),
  };
}

// ── Diff Data Pipeline (US5, T039) ───────────────────────────────────

/**
 * Fetch diff data for a device.
 * @param {string} device - Device hostname
 * @param {'config'|'routing'|'acl'} diffType - Type of diff
 * @returns {Promise<{ diff: object, dataSources: Array, warnings: Array }>}
 */
async function fetchDiffData(device, diffType) {
  const dataSources = [];
  const warnings = [];

  let currentTool, previousTool;
  if (diffType === 'config') {
    currentTool = 'pyats_show_running_config';
    previousTool = 'pyats_show_running_config';
  } else if (diffType === 'routing') {
    currentTool = 'pyats_show_ip_route';
    previousTool = 'pyats_show_ip_route';
  } else if (diffType === 'acl') {
    currentTool = 'pyats_show_access_lists';
    previousTool = 'pyats_show_access_lists';
  }

  // Fetch current state
  const currentResult = await invokeMcpTool('pyats', currentTool, { device });
  dataSources.push(currentResult.ref);

  // Fetch previous state (snapshot comparison)
  const previousResult = await invokeMcpTool('pyats', previousTool, {
    device,
    snapshot: 'previous',
  });
  dataSources.push(previousResult.ref);

  const currentText = extractTextContent(currentResult.data, device);
  const previousText = extractTextContent(previousResult.data, device);

  // Compute diff hunks
  const hunks = computeDiffHunks(previousText, currentText);

  const diff = {
    diffType,
    device,
    before: 'Previous',
    after: 'Current',
    hunks,
  };

  return { diff, dataSources, warnings };
}

/**
 * Extract text content from pyATS response for diff comparison.
 */
function extractTextContent(data, device) {
  if (!data) return '';
  const deviceData = data[device] || data.devices?.[device] || data;
  if (typeof deviceData === 'string') return deviceData;
  if (deviceData.config) return deviceData.config;
  if (deviceData.output) return deviceData.output;
  return JSON.stringify(deviceData, null, 2);
}

/**
 * Compute diff hunks between two text blocks.
 * Uses a simple line-by-line diff algorithm.
 * @param {string} before
 * @param {string} after
 * @returns {Array<{ header: string, lines: Array }>}
 */
function computeDiffHunks(before, after) {
  const beforeLines = (before || '').split('\n');
  const afterLines = (after || '').split('\n');
  const hunks = [];
  let currentHunk = null;

  // Simple diff: find added and removed lines
  const beforeSet = new Set(beforeLines.map((l, i) => `${i}:${l}`));
  const afterSet = new Set(afterLines.map((l, i) => `${i}:${l}`));

  const maxLen = Math.max(beforeLines.length, afterLines.length);
  let inDiff = false;

  for (let i = 0; i < maxLen; i++) {
    const bLine = i < beforeLines.length ? beforeLines[i] : null;
    const aLine = i < afterLines.length ? afterLines[i] : null;

    if (bLine === aLine) {
      if (inDiff && currentHunk) {
        // Add context line
        currentHunk.lines.push({
          type: 'context',
          content: aLine || '',
          lineNumber: i + 1,
        });
        // End hunk after 3 context lines
        if (currentHunk.lines.filter(l => l.type === 'context').length >= 3) {
          hunks.push(currentHunk);
          currentHunk = null;
          inDiff = false;
        }
      }
      continue;
    }

    if (!currentHunk) {
      // Start new hunk with context
      currentHunk = {
        header: `@@ line ${i + 1} @@`,
        lines: [],
      };
      // Add preceding context (up to 3 lines)
      for (let j = Math.max(0, i - 3); j < i; j++) {
        const ctxLine = j < beforeLines.length ? beforeLines[j] : (j < afterLines.length ? afterLines[j] : '');
        currentHunk.lines.push({
          type: 'context',
          content: ctxLine,
          lineNumber: j + 1,
        });
      }
    }

    inDiff = true;

    if (bLine !== null && (aLine === null || bLine !== aLine)) {
      currentHunk.lines.push({
        type: 'removed',
        content: bLine,
        lineNumber: i + 1,
      });
    }
    if (aLine !== null && (bLine === null || bLine !== aLine)) {
      currentHunk.lines.push({
        type: 'added',
        content: aLine,
        lineNumber: i + 1,
      });
    }
  }

  if (currentHunk && currentHunk.lines.length > 0) {
    hunks.push(currentHunk);
  }

  return hunks;
}

// ── Health Scorecard Data Pipeline (T043) ────────────────────────────

/**
 * Fetch and compute health scorecard data.
 * @param {string} target - Device or site name
 * @param {'site'|'device'} level
 * @returns {Promise<{ scorecard: object, dataSources: Array, warnings: Array }>}
 */
async function fetchScorecardData(target, level) {
  const dataSources = [];
  const warnings = [];
  const entries = [];

  // Fetch all health metrics
  const healthResult = await fetchHealthMetricsForNodes(
    level === 'site' ? [] : [target]
  );
  dataSources.push(...healthResult.dataSources);
  warnings.push(...healthResult.warnings);

  if (level === 'device') {
    const metrics = healthResult.metrics.get(target);
    const score = computeHealthScore(metrics);
    const indicators = buildHealthIndicators(metrics);
    const overallHealth = classifyScoreHealth(score);

    entries.push({
      name: target,
      overallHealth,
      score,
      indicators,
      drillDown: false,
    });
  } else {
    // Site level: would fetch all devices in the site and compute per-device scores
    // For now, create a placeholder that the topology data pipeline would populate
    const topoData = await fetchTopologyData({ sites: [target] });
    dataSources.push(...topoData.dataSources);

    for (const node of topoData.nodes) {
      const score = computeHealthScore(node.metrics);
      const indicators = buildHealthIndicators(node.metrics);

      entries.push({
        name: node.id,
        overallHealth: node.health,
        score,
        indicators,
        drillDown: true,
      });
    }
  }

  const scorecard = { level, entries };
  return { scorecard, dataSources, warnings };
}

/**
 * Compute weighted composite health score (0-100).
 * Weights: CPU 20%, Memory 20%, Interfaces 25%, BGP 20%, OSPF 15%.
 * Missing indicators are excluded and weights redistributed.
 * @param {object} metrics - NodeMetrics
 * @returns {number} Score 0-100
 */
function computeHealthScore(metrics) {
  if (!metrics) return 0;

  const weights = {
    cpu: 0.20,
    memory: 0.20,
    interfaces: 0.25,
    bgp: 0.20,
    ospf: 0.15,
  };

  const scores = {};
  let totalWeight = 0;

  // CPU score: 100 - cpu_percent
  if (metrics.cpuPercent !== null && metrics.cpuPercent !== undefined) {
    scores.cpu = 100 - metrics.cpuPercent;
    totalWeight += weights.cpu;
  }

  // Memory score: 100 - memory_percent
  if (metrics.memoryPercent !== null && metrics.memoryPercent !== undefined) {
    scores.memory = 100 - metrics.memoryPercent;
    totalWeight += weights.memory;
  }

  // Interface score: assume healthy = 100 (no errors = perfect)
  if (metrics.interfaceErrors !== null && metrics.interfaceErrors !== undefined) {
    scores.interfaces = metrics.interfaceErrors === 0 ? 100 :
                       metrics.interfaceErrors < 10 ? 80 :
                       metrics.interfaceErrors < 100 ? 50 : 20;
    totalWeight += weights.interfaces;
  }

  // BGP score: (established/total) * 100
  if (metrics.bgpPeersTotal > 0) {
    scores.bgp = ((metrics.bgpPeersUp || 0) / metrics.bgpPeersTotal) * 100;
    totalWeight += weights.bgp;
  }

  // OSPF score: adjacencies up > 0 = healthy
  if (metrics.ospfAdjacenciesUp !== null && metrics.ospfAdjacenciesUp !== undefined) {
    scores.ospf = metrics.ospfAdjacenciesUp > 0 ? 100 : 0;
    totalWeight += weights.ospf;
  }

  if (totalWeight === 0) return 0;

  // Redistribute weights proportionally
  let weightedSum = 0;
  for (const [key, score] of Object.entries(scores)) {
    weightedSum += score * (weights[key] / totalWeight);
  }

  return Math.round(weightedSum);
}

/**
 * Classify a health score into a health status.
 */
function classifyScoreHealth(score) {
  if (score >= 70) return 'healthy';
  if (score >= 40) return 'warning';
  if (score > 0) return 'critical';
  return 'unknown';
}

/**
 * Build health indicator badges from metrics.
 */
function buildHealthIndicators(metrics) {
  if (!metrics) return [];
  const indicators = [];

  if (metrics.cpuPercent !== null && metrics.cpuPercent !== undefined) {
    indicators.push({
      name: 'CPU',
      status: classifyHealth(metrics.cpuPercent),
      value: `${metrics.cpuPercent}%`,
    });
  }

  if (metrics.memoryPercent !== null && metrics.memoryPercent !== undefined) {
    indicators.push({
      name: 'Memory',
      status: classifyHealth(metrics.memoryPercent),
      value: `${metrics.memoryPercent}%`,
    });
  }

  if (metrics.interfaceErrors !== null && metrics.interfaceErrors !== undefined) {
    const status = metrics.interfaceErrors === 0 ? 'healthy' :
                  metrics.interfaceErrors < 100 ? 'warning' : 'critical';
    indicators.push({
      name: 'Interfaces',
      status,
      value: `${metrics.interfaceErrors} errors`,
    });
  }

  if (metrics.bgpPeersTotal > 0) {
    const status = metrics.bgpPeersUp === metrics.bgpPeersTotal ? 'healthy' :
                  metrics.bgpPeersUp > 0 ? 'warning' : 'critical';
    indicators.push({
      name: 'BGP',
      status,
      value: `${metrics.bgpPeersUp}/${metrics.bgpPeersTotal}`,
    });
  }

  if (metrics.ospfAdjacenciesUp !== null && metrics.ospfAdjacenciesUp !== undefined) {
    indicators.push({
      name: 'OSPF',
      status: metrics.ospfAdjacenciesUp > 0 ? 'healthy' : 'warning',
      value: `${metrics.ospfAdjacenciesUp} full`,
    });
  }

  return indicators;
}

export {
  invokeMcpTool,
  fetchTopologyData,
  fetchDashboardData,
  fetchAlertData,
  fetchChangeData,
  fetchPathTraceData,
  fetchDiffData,
  fetchScorecardData,
  computeHealthScore,
  computeDiffHunks,
  processNeighborData,
  processGrafanaAlerts,
  processPrometheusAlerts,
  processSyslogAlerts,
  createDataSourceRef,
  inferDeviceRole,
};
