/**
 * graph-layout.js — Force-directed and hierarchical layout engine.
 *
 * Provides two layout algorithms:
 * 1. Force-directed: For arbitrary topologies (mesh, ring, etc.)
 * 2. Hierarchical: For structured fabrics with spine/leaf detection
 *
 * Supports up to 500 nodes. Automatically selects hierarchical layout
 * when spine/leaf roles are detected in the topology.
 */

// Layout configuration
const CONFIG = {
  // Force-directed parameters
  force: {
    repulsion: 5000,       // Node repulsion strength
    attraction: 0.01,      // Edge attraction strength
    damping: 0.85,         // Velocity damping per iteration
    minDistance: 80,        // Minimum node distance
    maxIterations: 300,     // Max simulation iterations
    convergenceThreshold: 0.5, // Stop when total movement < this
  },
  // Hierarchical layout parameters
  hierarchical: {
    levelHeight: 150,      // Vertical spacing between levels
    nodeSpacing: 120,      // Horizontal spacing between nodes at same level
    padding: 60,           // Canvas padding
  },
  // Canvas dimensions
  canvas: {
    width: 1200,
    height: 800,
  },
};

/**
 * Auto-detect and apply the best layout algorithm for the topology.
 * Uses hierarchical layout if spine/leaf roles are detected,
 * force-directed otherwise.
 *
 * @param {Array<object>} nodes - TopologyNode[] with id, role properties
 * @param {Array<object>} edges - TopologyEdge[] with source, target properties
 * @param {object} [options] - Override layout options
 * @returns {Array<object>} Nodes with x, y positions set
 */
function applyLayout(nodes, edges, options = {}) {
  if (!nodes || nodes.length === 0) return [];

  const width = options.width || CONFIG.canvas.width;
  const height = options.height || CONFIG.canvas.height;

  // Detect if this is a structured fabric (spine/leaf)
  const hasSpineLeaf = detectSpineLeafTopology(nodes);

  if (hasSpineLeaf) {
    return applyHierarchicalLayout(nodes, edges, width, height);
  }

  return applyForceDirectedLayout(nodes, edges, width, height);
}

/**
 * Detect if the topology has a spine/leaf structure.
 * @param {Array<object>} nodes
 * @returns {boolean}
 */
function detectSpineLeafTopology(nodes) {
  const roles = new Set(nodes.map(n => (n.role || '').toLowerCase()));
  return roles.has('spine') && roles.has('leaf');
}

/**
 * Apply hierarchical layout for structured fabrics.
 * Levels: superspine -> spine -> leaf -> access/host
 *
 * @param {Array<object>} nodes
 * @param {Array<object>} edges
 * @param {number} width
 * @param {number} height
 * @returns {Array<object>} Nodes with positions
 */
function applyHierarchicalLayout(nodes, edges, width, height) {
  const { levelHeight, nodeSpacing, padding } = CONFIG.hierarchical;

  // Assign levels based on role
  const levelMap = {
    superspine: 0,
    spine: 1,
    border: 1,
    core: 1,
    leaf: 2,
    distribution: 2,
    access: 3,
    switch: 3,
    host: 4,
    server: 4,
  };

  // Group nodes by level
  const levels = new Map();
  for (const node of nodes) {
    const role = (node.role || 'unknown').toLowerCase();
    const level = levelMap[role] !== undefined ? levelMap[role] : 3;
    if (!levels.has(level)) levels.set(level, []);
    levels.get(level).push(node);
  }

  // Sort levels
  const sortedLevels = [...levels.entries()].sort((a, b) => a[0] - b[0]);
  const totalLevels = sortedLevels.length;

  // Position nodes
  for (let li = 0; li < sortedLevels.length; li++) {
    const [level, levelNodes] = sortedLevels[li];
    const y = padding + (li / Math.max(1, totalLevels - 1)) * (height - 2 * padding);
    const totalWidth = (levelNodes.length - 1) * nodeSpacing;
    const startX = (width - totalWidth) / 2;

    for (let ni = 0; ni < levelNodes.length; ni++) {
      levelNodes[ni].x = startX + ni * nodeSpacing;
      levelNodes[ni].y = y;
    }
  }

  return nodes;
}

/**
 * Apply force-directed layout for arbitrary topologies.
 * Uses a simplified Fruchterman-Reingold algorithm.
 *
 * @param {Array<object>} nodes
 * @param {Array<object>} edges
 * @param {number} width
 * @param {number} height
 * @returns {Array<object>} Nodes with positions
 */
function applyForceDirectedLayout(nodes, edges, width, height) {
  const { repulsion, attraction, damping, minDistance, maxIterations, convergenceThreshold } = CONFIG.force;

  // Build adjacency for quick edge lookup
  const adjacency = new Map();
  for (const edge of edges) {
    if (!adjacency.has(edge.source)) adjacency.set(edge.source, []);
    if (!adjacency.has(edge.target)) adjacency.set(edge.target, []);
    adjacency.get(edge.source).push(edge.target);
    adjacency.get(edge.target).push(edge.source);
  }

  // Initialize positions randomly within canvas
  const padding = 60;
  const nodePositions = new Map();

  for (const node of nodes) {
    if (node.x !== null && node.x !== undefined && node.y !== null && node.y !== undefined) {
      nodePositions.set(node.id, { x: node.x, y: node.y, vx: 0, vy: 0 });
    } else {
      nodePositions.set(node.id, {
        x: padding + Math.random() * (width - 2 * padding),
        y: padding + Math.random() * (height - 2 * padding),
        vx: 0,
        vy: 0,
      });
    }
  }

  // Optimal distance based on canvas area and node count
  const area = (width - 2 * padding) * (height - 2 * padding);
  const k = Math.sqrt(area / Math.max(1, nodes.length));

  // Simulation loop
  let temperature = width / 10;
  const cooling = temperature / (maxIterations + 1);

  for (let iter = 0; iter < maxIterations; iter++) {
    let totalMovement = 0;

    // Calculate repulsive forces (all pairs)
    const forces = new Map();
    for (const node of nodes) {
      forces.set(node.id, { fx: 0, fy: 0 });
    }

    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const pi = nodePositions.get(nodes[i].id);
        const pj = nodePositions.get(nodes[j].id);

        let dx = pi.x - pj.x;
        let dy = pi.y - pj.y;
        let dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 1) { dist = 1; dx = 1; dy = 0; }

        // Repulsive force: k^2 / distance
        const force = (k * k) / dist;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;

        forces.get(nodes[i].id).fx += fx;
        forces.get(nodes[i].id).fy += fy;
        forces.get(nodes[j].id).fx -= fx;
        forces.get(nodes[j].id).fy -= fy;
      }
    }

    // Calculate attractive forces (edges only)
    for (const edge of edges) {
      const pi = nodePositions.get(edge.source);
      const pj = nodePositions.get(edge.target);
      if (!pi || !pj) continue;

      let dx = pi.x - pj.x;
      let dy = pi.y - pj.y;
      let dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 1) dist = 1;

      // Attractive force: distance^2 / k
      const force = (dist * dist) / k;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;

      if (forces.has(edge.source)) {
        forces.get(edge.source).fx -= fx;
        forces.get(edge.source).fy -= fy;
      }
      if (forces.has(edge.target)) {
        forces.get(edge.target).fx += fx;
        forces.get(edge.target).fy += fy;
      }
    }

    // Apply forces with temperature limiting
    for (const node of nodes) {
      const pos = nodePositions.get(node.id);
      const f = forces.get(node.id);
      if (!pos || !f) continue;

      const fMag = Math.sqrt(f.fx * f.fx + f.fy * f.fy);
      if (fMag < 0.001) continue;

      // Limit displacement to temperature
      const disp = Math.min(fMag, temperature);
      const dx = (f.fx / fMag) * disp;
      const dy = (f.fy / fMag) * disp;

      pos.x += dx;
      pos.y += dy;

      // Keep within bounds
      pos.x = Math.max(padding, Math.min(width - padding, pos.x));
      pos.y = Math.max(padding, Math.min(height - padding, pos.y));

      totalMovement += Math.abs(dx) + Math.abs(dy);
    }

    // Cool down
    temperature -= cooling;
    if (temperature < 0) temperature = 0;

    // Check convergence
    if (totalMovement < convergenceThreshold) break;
  }

  // Write positions back to nodes
  for (const node of nodes) {
    const pos = nodePositions.get(node.id);
    if (pos) {
      node.x = Math.round(pos.x);
      node.y = Math.round(pos.y);
    }
  }

  return nodes;
}

/**
 * Apply cluster-based layout for site groupings.
 * Positions clusters in a grid, then applies force-directed within each cluster.
 *
 * @param {Array<object>} nodes - TopologyNode[]
 * @param {Array<object>} edges - TopologyEdge[]
 * @param {Array<object>} clusters - TopologyCluster[] with nodeIds
 * @param {number} [width] - Canvas width
 * @param {number} [height] - Canvas height
 * @returns {{ nodes: Array, clusters: Array }} Positioned nodes and cluster bounds
 */
function applyClusterLayout(nodes, edges, clusters, width, height) {
  width = width || CONFIG.canvas.width;
  height = height || CONFIG.canvas.height;

  if (!clusters || clusters.length === 0) {
    return { nodes: applyLayout(nodes, edges, { width, height }), clusters: [] };
  }

  // Calculate cluster grid
  const cols = Math.ceil(Math.sqrt(clusters.length));
  const rows = Math.ceil(clusters.length / cols);
  const cellWidth = width / cols;
  const cellHeight = height / rows;
  const clusterPadding = 20;

  const positionedClusters = [];

  for (let ci = 0; ci < clusters.length; ci++) {
    const cluster = clusters[ci];
    const col = ci % cols;
    const row = Math.floor(ci / cols);

    const cellX = col * cellWidth + clusterPadding;
    const cellY = row * cellHeight + clusterPadding;
    const innerWidth = cellWidth - 2 * clusterPadding;
    const innerHeight = cellHeight - 2 * clusterPadding;

    // Get cluster nodes and internal edges
    const nodeIds = new Set(cluster.nodeIds);
    const clusterNodes = nodes.filter(n => nodeIds.has(n.id));
    const clusterEdges = edges.filter(e => nodeIds.has(e.source) && nodeIds.has(e.target));

    // Apply layout within cluster bounds
    const laid = applyLayout(clusterNodes, clusterEdges, {
      width: innerWidth,
      height: innerHeight,
    });

    // Offset to cluster position
    for (const node of laid) {
      node.x = (node.x || 0) + cellX;
      node.y = (node.y || 0) + cellY;
    }

    positionedClusters.push({
      ...cluster,
      bounds: {
        x: cellX - clusterPadding / 2,
        y: cellY - clusterPadding / 2,
        width: cellWidth - clusterPadding,
        height: cellHeight - clusterPadding,
      },
    });
  }

  return { nodes, clusters: positionedClusters };
}

export {
  applyLayout,
  applyForceDirectedLayout,
  applyHierarchicalLayout,
  applyClusterLayout,
  detectSpineLeafTopology,
  CONFIG,
};
