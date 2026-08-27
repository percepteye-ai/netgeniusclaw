/**
 * topology-map.js — Canvas component for network topology visualization.
 *
 * Accepts TopologyContent data model (nodes, edges, clusters, legend).
 * Applies graph-layout.js positioning, renders nodes with health-colored fills,
 * renders edges with interface labels, and includes an expandable color legend.
 *
 * Handles: site-based clustering (T012), topology filtering (T013),
 * graceful degradation (T014), and empty-data handling (T015).
 */

import { applyLayout, applyClusterLayout } from '../lib/graph-layout.js';
import { getHealthFill, getHealthStroke, getEdgeColor, buildHealthLegend } from '../lib/color-scale.js';
import { filterNodes, filterEdges, describeFilters, hasActiveFilters } from '../lib/filter-engine.js';
import { buildA2UIEnvelope, buildErrorCard, createWarning } from '../lib/a2ui-renderer.js';
import { fetchTopologyData } from '../lib/data-fetcher.js';

// Maximum nodes before automatic clustering
const CLUSTER_THRESHOLD = 200;

/**
 * Render a topology map visualization.
 *
 * @param {object} options
 * @param {object} [options.scope] - Scope filters
 * @param {string} [options.title] - Override title
 * @returns {object} A2UI JSON envelope
 */
async function renderTopologyMap(options = {}) {
  const { scope, title } = options;

  // Fetch topology data from MCP servers
  const result = await fetchTopologyData(scope);
  let { nodes, edges, dataSources, warnings } = result;

  // T015: Empty-data handling
  if (nodes.length === 0) {
    return buildErrorCard({
      title: 'No Topology Data Available',
      message: 'No CDP/LLDP discovery data was found. Topology visualization requires neighbor discovery data.',
      suggestion: 'Run a CDP/LLDP discovery operation first, then try "show me the network topology" again.',
    });
  }

  // T013: Apply scope filtering
  if (scope && hasActiveFilters(scope)) {
    const unfilteredCount = nodes.length;
    nodes = filterNodes(nodes, scope);
    edges = filterEdges(edges, nodes);

    if (nodes.length === 0) {
      return buildErrorCard({
        title: 'No Devices Match Filter',
        message: `No devices match the filter: ${describeFilters(scope)}. ${unfilteredCount} devices exist in the full topology.`,
        suggestion: 'Try a broader filter or remove filters to see the full topology.',
      });
    }

    if (nodes.length < unfilteredCount) {
      warnings.push(createWarning('info',
        `Showing ${nodes.length} of ${unfilteredCount} devices (${describeFilters(scope)})`,
        'filter-engine'));
    }
  }

  // T014: Graceful degradation - check if health data is available
  const hasHealthData = nodes.some(n => n.health !== 'unknown');
  if (!hasHealthData) {
    warnings.push(createWarning('warning',
      'Health metric sources unavailable. All devices shown with unknown (gray) status.',
      'health-metrics'));
  }

  // T012: Site-based clustering for large topologies
  let clusters = [];
  if (nodes.length > CLUSTER_THRESHOLD) {
    clusters = buildSiteClusters(nodes);
    if (clusters.length > 0) {
      const layoutResult = applyClusterLayout(nodes, edges, clusters);
      nodes = layoutResult.nodes;
      clusters = layoutResult.clusters;
    } else {
      warnings.push(createWarning('info',
        `Large topology (${nodes.length} devices) without site metadata. Consider adding site data for better visualization.`,
        'clustering'));
      nodes = applyLayout(nodes, edges);
    }
  } else {
    nodes = applyLayout(nodes, edges);
  }

  // Build legend
  const legend = buildHealthLegend();

  // Build content
  const content = {
    nodes,
    edges,
    clusters,
    legend,
  };

  return buildA2UIEnvelope({
    component: 'topology-map',
    title: title || 'Network Topology',
    dataSources,
    scope: scope || {},
    warnings,
    content,
  });
}

/**
 * Build site-based clusters from node site metadata.
 * @param {Array<object>} nodes - TopologyNode[]
 * @returns {Array<object>} TopologyCluster[]
 */
function buildSiteClusters(nodes) {
  const siteMap = new Map();

  for (const node of nodes) {
    if (!node.site) continue;
    if (!siteMap.has(node.site)) {
      siteMap.set(node.site, []);
    }
    siteMap.get(node.site).push(node.id);
  }

  // Only cluster if we have meaningful site data
  if (siteMap.size < 2) return [];

  return [...siteMap.entries()].map(([site, nodeIds]) => ({
    id: site,
    label: site,
    nodeIds,
    expanded: nodeIds.length <= 50, // Auto-expand small clusters
  }));
}

/**
 * Render the topology map as HTML for Canvas embedding.
 * @param {object} content - TopologyContent
 * @param {Array} [allWarnings] - Warning[]
 * @returns {string} HTML string
 */
function renderTopologyHTML(content, allWarnings = []) {
  const { nodes, edges, clusters, legend } = content;
  const width = 1200;
  const height = 800;

  let html = '<div class="topology-map">';

  // Warning banners
  for (const w of allWarnings) {
    if (w.level === 'warning' || w.level === 'error') {
      html += `<div class="topology-warning"><span class="topology-warning__icon"></span>${escapeHtml(w.message)}</div>`;
    }
  }

  // SVG canvas
  html += `<svg class="topology-map__canvas" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">`;

  // Render clusters
  for (const cluster of clusters) {
    if (cluster.bounds) {
      html += `<rect class="topology-cluster" x="${cluster.bounds.x}" y="${cluster.bounds.y}" ` +
              `width="${cluster.bounds.width}" height="${cluster.bounds.height}" />`;
      html += `<text class="topology-cluster__label" x="${cluster.bounds.x + 8}" y="${cluster.bounds.y + 18}">${escapeHtml(cluster.label)}</text>`;
    }
  }

  // Render edges
  for (const edge of edges) {
    const source = nodes.find(n => n.id === edge.source);
    const target = nodes.find(n => n.id === edge.target);
    if (!source || !target || source.x == null || target.x == null) continue;

    const color = getEdgeColor(edge.status);
    const statusClass = `topology-edge--${edge.status}`;
    html += `<line class="topology-edge ${statusClass}" x1="${source.x}" y1="${source.y}" x2="${target.x}" y2="${target.y}" stroke="${color}" />`;

    // Interface labels at midpoint
    const mx = (source.x + target.x) / 2;
    const my = (source.y + target.y) / 2;
    const label = edge.sourceInterface && edge.targetInterface
      ? `${edge.sourceInterface} - ${edge.targetInterface}`
      : edge.sourceInterface || edge.targetInterface || '';
    if (label) {
      html += `<text class="topology-edge__label" x="${mx}" y="${my - 4}">${escapeHtml(label)}</text>`;
    }
  }

  // Render nodes
  for (const node of nodes) {
    if (node.x == null || node.y == null) continue;

    const fill = getHealthFill(node.health);
    const stroke = getHealthStroke(node.health);
    const healthClass = `topology-node--${node.health}`;

    html += `<g class="topology-node ${healthClass}" data-id="${escapeHtml(node.id)}">`;
    html += `<circle class="topology-node__circle" cx="${node.x}" cy="${node.y}" r="18" fill="${fill}" stroke="${stroke}" />`;
    html += `<text class="topology-node__label" x="${node.x}" y="${node.y + 30}">${escapeHtml(node.label)}</text>`;
    if (node.role) {
      html += `<text class="topology-node__role" x="${node.x}" y="${node.y + 42}">${escapeHtml(node.role)}</text>`;
    }
    html += '</g>';
  }

  html += '</svg>';

  // Legend overlay
  html += '<div class="topology-legend">';
  html += '<div class="topology-legend__title">Health Status</div>';
  for (const entry of legend) {
    html += '<div class="topology-legend__item">';
    html += `<span class="topology-legend__swatch" style="background:${entry.color}; border-color:${entry.color}"></span>`;
    html += `<span class="topology-legend__label">${escapeHtml(entry.label)}</span>`;
    html += '</div>';
  }
  html += '</div>';

  html += '</div>';
  return html;
}

/**
 * Escape HTML entities.
 */
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

export {
  renderTopologyMap,
  renderTopologyHTML,
  buildSiteClusters,
  CLUSTER_THRESHOLD,
};
