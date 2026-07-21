import { GraphData, GraphNode } from "./types";

const COLUMN_WIDTH = 260;
const ROW_HEIGHT = 90;

/**
 * Computes a left-to-right layered layout: modules are placed in columns
 * based on their shortest directed distance to any infra node (database,
 * cache, queue, external_api). Infra nodes sit in the rightmost column.
 * This mimics an architecture diagram flowing from entry points to infra,
 * rather than a generic force-directed hairball.
 */
export function computeLayout(graph: GraphData): Record<string, { x: number; y: number }> {
  const infraTypes = new Set(["database", "cache", "queue", "external_api", "service"]);
  const infraIds = graph.nodes.filter((n) => infraTypes.has(n.type)).map((n) => n.id);

  const adjacency = new Map<string, string[]>();
  graph.nodes.forEach((n) => adjacency.set(n.id, []));
  graph.edges.forEach((e) => {
    adjacency.get(e.source)?.push(e.target);
  });

  // BFS distance from each node to the nearest infra node, following edges forward.
  const distToInfra = new Map<string, number>();
  infraIds.forEach((id) => distToInfra.set(id, 0));

  const moduleIds = graph.nodes.filter((n) => !infraTypes.has(n.type)).map((n) => n.id);
  // Reverse BFS: start from infra nodes, walk edges backward to find distance
  const reverseAdjacency = new Map<string, string[]>();
  graph.nodes.forEach((n) => reverseAdjacency.set(n.id, []));
  graph.edges.forEach((e) => {
    reverseAdjacency.get(e.target)?.push(e.source);
  });

  const queue: string[] = [...infraIds];
  const visited = new Set(infraIds);
  while (queue.length > 0) {
    const current = queue.shift()!;
    const d = distToInfra.get(current)!;
    for (const prev of reverseAdjacency.get(current) || []) {
      if (!visited.has(prev)) {
        visited.add(prev);
        distToInfra.set(prev, d + 1);
        queue.push(prev);
      }
    }
  }

  const maxModuleDist = Math.max(0, ...moduleIds.map((id) => distToInfra.get(id) ?? 0));

  // Column: modules unreachable to infra get column 0 (leftmost / entry points).
  // Modules closer to infra get higher column numbers. Infra itself is the last column.
  const columnOf = (n: GraphNode): number => {
    if (infraTypes.has(n.type)) return maxModuleDist + 1;
    const d = distToInfra.get(n.id);
    if (d === undefined) return 0;
    return maxModuleDist - d;
  };

  const columns = new Map<number, GraphNode[]>();
  graph.nodes.forEach((n) => {
    const col = columnOf(n);
    if (!columns.has(col)) columns.set(col, []);
    columns.get(col)!.push(n);
  });

  const positions: Record<string, { x: number; y: number }> = {};
  columns.forEach((nodesInCol, col) => {
    nodesInCol.sort((a, b) => a.label.localeCompare(b.label));
    nodesInCol.forEach((n, i) => {
      positions[n.id] = {
        x: col * COLUMN_WIDTH,
        y: i * ROW_HEIGHT,
      };
    });
  });

  return positions;
}
