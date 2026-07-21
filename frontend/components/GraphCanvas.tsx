"use client";

import { useMemo } from "react";
import ReactFlow, {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  Node,
  Edge,
  MarkerType,
} from "reactflow";
import "reactflow/dist/style.css";
import { GraphData } from "@/lib/types";
import { computeLayout } from "@/lib/layout";
import TwinNode from "./TwinNode";

const nodeTypes = { twin: TwinNode };

interface GraphCanvasProps {
  graph: GraphData;
  highlightedNodeIds: Set<string>;
  targetNodeId: string | null;
  riskLevel: string | null;
  highlightedEdgeIds: Set<string>;
}

export default function GraphCanvas({
  graph,
  highlightedNodeIds,
  targetNodeId,
  riskLevel,
  highlightedEdgeIds,
}: GraphCanvasProps) {
  const positions = useMemo(() => computeLayout(graph), [graph]);

  const nodes: Node[] = useMemo(
    () =>
      graph.nodes.map((n) => ({
        id: n.id,
        type: "twin",
        position: positions[n.id] || { x: 0, y: 0 },
        data: {
          label: n.label,
          nodeType: n.type,
          color: n.color,
          fileHint: n.file,
          highlighted: highlightedNodeIds.has(n.id),
          isTarget: n.id === targetNodeId,
          riskLevel: riskLevel || "medium",
        },
      })),
    [graph, positions, highlightedNodeIds, targetNodeId, riskLevel]
  );

  const edges: Edge[] = useMemo(
    () =>
      graph.edges.map((e) => {
        const isHighlighted = highlightedEdgeIds.has(e.id);
        return {
          id: e.id,
          source: e.source,
          target: e.target,
          animated: isHighlighted,
          className: isHighlighted ? "edge-highlighted" : "",
          markerEnd: { type: MarkerType.ArrowClosed, color: isHighlighted ? "#4FD1C5" : "#3a4552" },
          style: { strokeWidth: isHighlighted ? 2.5 : 1.2 },
        };
      }),
    [graph, highlightedEdgeIds]
  );

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      fitView
      minZoom={0.2}
      maxZoom={1.5}
      proOptions={{ hideAttribution: true }}
    >
      <Background variant={BackgroundVariant.Dots} color="#1c232d" gap={24} size={1} />
      <Controls showInteractive={false} />
      <MiniMap
        nodeColor={(n) => (n.data as any)?.color || "#4b5563"}
        maskColor="rgba(11,15,20,0.7)"
      />
    </ReactFlow>
  );
}
