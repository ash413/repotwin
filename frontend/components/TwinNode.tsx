"use client";

import { Handle, Position } from "reactflow";

const TYPE_ICON: Record<string, string> = {
  module: "▢",
  service: "◆",
  database: "▤",
  cache: "◈",
  queue: "▥",
  external_api: "◇",
};

const RISK_RING: Record<string, string> = {
  critical: "ring-2 ring-risk-critical shadow-[0_0_16px_rgba(248,113,113,0.55)]",
  high: "ring-2 ring-risk-high shadow-[0_0_16px_rgba(251,146,60,0.5)]",
  medium: "ring-2 ring-risk-medium shadow-[0_0_16px_rgba(251,191,36,0.45)]",
  low: "ring-2 ring-risk-low shadow-[0_0_16px_rgba(52,211,153,0.4)]",
};

export interface TwinNodeData {
  label: string;
  nodeType: string;
  color: string;
  highlighted?: boolean;
  isTarget?: boolean;
  riskLevel?: string;
  fileHint?: string | null;
}

export default function TwinNode({ data }: { data: TwinNodeData }) {
  const highlightClasses = data.highlighted
    ? `${RISK_RING[data.riskLevel || "medium"]} ${data.isTarget ? "animate-pulseglow" : ""}`
    : "";

  return (
    <div
      className={`px-3 py-2 rounded-lg border transition-all duration-300 min-w-[150px] ${
        data.highlighted
          ? "bg-surface2 border-accent/60 opacity-100"
          : "bg-surface border-border opacity-90"
      } ${highlightClasses}`}
    >
      <Handle type="target" position={Position.Left} className="!bg-border !w-1.5 !h-1.5" />
      <div className="flex items-center gap-2">
        <span
          className="text-xs w-5 h-5 flex items-center justify-center rounded"
          style={{ color: data.color, backgroundColor: `${data.color}22` }}
        >
          {TYPE_ICON[data.nodeType] || "▢"}
        </span>
        <div className="min-w-0">
          <div className="text-sm font-medium text-text truncate max-w-[140px]">{data.label}</div>
          {data.fileHint && (
            <div className="text-[10px] text-muted font-mono truncate max-w-[140px]">
              {data.fileHint}
            </div>
          )}
        </div>
      </div>
      <Handle type="source" position={Position.Right} className="!bg-border !w-1.5 !h-1.5" />
    </div>
  );
}
