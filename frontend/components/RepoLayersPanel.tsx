"use client";

import { useState } from "react";
import { GraphData, HealthReport } from "@/lib/types";

const TYPE_LABELS: Record<string, string> = {
  module: "Modules",
  service: "Services",
  database: "Databases",
  cache: "Caches",
  queue: "Queues",
  external_api: "External APIs",
};

const TYPE_COLORS: Record<string, string> = {
  module: "#6366f1",
  service: "#0ea5e9",
  database: "#16a34a",
  cache: "#dc2626",
  queue: "#d97706",
  external_api: "#9333ea",
};

interface RepoLayersPanelProps {
  graph: GraphData | null;
  health: HealthReport | null;
  scanning: boolean;
  onScanDemo: () => void;
  onScanPath: (path: string) => void;
}

export default function RepoLayersPanel({
  graph,
  health,
  scanning,
  onScanDemo,
  onScanPath,
}: RepoLayersPanelProps) {
  const [pathInput, setPathInput] = useState("");

  const counts: Record<string, number> = {};
  graph?.nodes.forEach((n) => {
    counts[n.type] = (counts[n.type] || 0) + 1;
  });

  return (
    <div className="h-full flex flex-col bg-surface border-r border-border overflow-y-auto">
      <div className="p-4 border-b border-border">
        <div className="text-xs uppercase tracking-wider text-muted mb-1">RepoTwin</div>
        <div className="text-lg font-semibold text-text">Repository</div>
      </div>

      <div className="p-4 border-b border-border space-y-2">
        <button
          onClick={onScanDemo}
          disabled={scanning}
          className="w-full text-sm font-medium bg-accent/15 text-accent border border-accent/40 rounded-md py-2 hover:bg-accent/25 transition-colors disabled:opacity-50"
        >
          {scanning ? "Scanning…" : "Scan demo repository"}
        </button>
        <div className="flex gap-2">
          <input
            value={pathInput}
            onChange={(e) => setPathInput(e.target.value)}
            placeholder="/path/to/repo"
            className="flex-1 bg-canvas border border-border rounded-md px-2 py-1.5 text-xs text-text font-mono placeholder:text-muted focus:outline-none focus:border-accent/60"
          />
          <button
            onClick={() => pathInput && onScanPath(pathInput)}
            disabled={scanning || !pathInput}
            className="text-xs px-3 rounded-md border border-border text-muted hover:text-text hover:border-accent/40 disabled:opacity-40"
          >
            Scan
          </button>
        </div>
      </div>

      {graph && (
        <div className="p-4 border-b border-border">
          <div className="text-xs uppercase tracking-wider text-muted mb-3">
            Architecture layers
          </div>
          <div className="space-y-2">
            {Object.entries(TYPE_LABELS).map(([type, label]) => (
              <div key={type} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: TYPE_COLORS[type] }}
                  />
                  <span className="text-text/90">{label}</span>
                </div>
                <span className="text-muted font-mono text-xs">{counts[type] || 0}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {health && (
        <div className="p-4 space-y-4">
          <div className="text-xs uppercase tracking-wider text-muted">Architecture health</div>

          <ScoreRow
            label="Single points of failure"
            value={health.summary.spof_count}
            danger={health.summary.spof_count > 0}
          />
          <ScoreRow
            label="Circular dependencies"
            value={health.summary.cycle_count}
            danger={health.summary.cycle_count > 0}
          />
          <ScoreRow label="Orphaned modules" value={health.orphaned_modules.length} />

          {health.single_points_of_failure.length > 0 && (
            <div>
              <div className="text-xs text-muted mb-1.5">Single points of failure</div>
              <div className="space-y-1.5">
                {health.single_points_of_failure.map((s) => (
                  <div
                    key={s.node}
                    className="text-xs font-mono bg-canvas border border-risk-high/30 text-risk-high/90 rounded px-2 py-1"
                  >
                    {s.node} · {s.dependents} dependents
                  </div>
                ))}
              </div>
            </div>
          )}

          {health.high_coupling_modules.length > 0 && (
            <div>
              <div className="text-xs text-muted mb-1.5">Highest coupling</div>
              <div className="space-y-1.5">
                {health.high_coupling_modules.slice(0, 4).map((m) => (
                  <div
                    key={m.module}
                    className="flex justify-between text-xs font-mono bg-canvas border border-border rounded px-2 py-1"
                  >
                    <span className="text-text/80 truncate">{m.module}</span>
                    <span className="text-muted">{m.degree}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {!graph && (
        <div className="p-4 text-sm text-muted leading-relaxed">
          Scan a repository to build its living architecture model — every
          service, database, queue, and dependency, traced from the actual
          code.
        </div>
      )}
    </div>
  );
}

function ScoreRow({
  label,
  value,
  danger,
}: {
  label: string;
  value: number;
  danger?: boolean;
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-text/80">{label}</span>
      <span
        className={`text-sm font-mono px-2 py-0.5 rounded ${
          danger ? "bg-risk-high/15 text-risk-high" : "bg-canvas text-muted"
        }`}
      >
        {value}
      </span>
    </div>
  );
}
