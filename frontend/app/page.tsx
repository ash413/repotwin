"use client";

import { useEffect, useRef, useState } from "react";
import GraphCanvas from "@/components/GraphCanvas";
import RepoLayersPanel from "@/components/RepoLayersPanel";
import InvestigationPanel from "@/components/InvestigationPanel";
import { scanDemo, scanPath, investigate, getHealthReport } from "@/lib/api";
import { GraphData, HealthReport, InvestigateResponse } from "@/lib/types";

const REVEAL_STEP_MS = 220;

export default function Home() {
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthReport | null>(null);
  const [scanning, setScanning] = useState(false);
  const [investigating, setInvestigating] = useState(false);
  const [result, setResult] = useState<InvestigateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [revealedIds, setRevealedIds] = useState<Set<string>>(new Set());
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);

  const clearTimers = () => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
  };

  useEffect(() => clearTimers, []);

  async function handleScan(scanFn: () => Promise<{ session_id: string; graph: GraphData }>) {
    setScanning(true);
    setError(null);
    setResult(null);
    setRevealedIds(new Set());
    try {
      const res = await scanFn();
      setGraph(res.graph);
      setSessionId(res.session_id);
      const h = await getHealthReport(res.session_id);
      setHealth(h);
    } catch (e: any) {
      setError(e.message || "Scan failed");
    } finally {
      setScanning(false);
    }
  }

  async function handleAsk(question: string) {
    if (!sessionId) return;
    clearTimers();
    setRevealedIds(new Set());
    setInvestigating(true);
    setError(null);
    try {
      const res = await investigate(sessionId, question);
      setResult(res);

      if (res.report && res.resolved_node) {
        // Reveal target, then direct dependents, then transitive dependents,
        // one at a time — makes the investigation visually "happen" rather
        // than just appearing.
        const order = [
          res.resolved_node,
          ...res.report.directly_affected
            .sort((a, b) => a.distance - b.distance)
            .map((m) => m.node_id),
          ...res.report.transitively_affected
            .sort((a, b) => a.distance - b.distance)
            .map((m) => m.node_id),
        ];
        order.forEach((id, i) => {
          const t = setTimeout(() => {
            setRevealedIds((prev) => new Set(prev).add(id));
          }, i * REVEAL_STEP_MS);
          timers.current.push(t);
        });
      }
    } catch (e: any) {
      setError(e.message || "Investigation failed");
    } finally {
      setInvestigating(false);
    }
  }

  const highlightedEdgeIds = new Set<string>();
  if (graph) {
    graph.edges.forEach((e) => {
      if (revealedIds.has(e.source) && revealedIds.has(e.target)) {
        highlightedEdgeIds.add(e.id);
      }
    });
  }

  return (
    <main className="h-screen w-screen grid grid-cols-[280px_1fr_380px] bg-canvas">
      <RepoLayersPanel
        graph={graph}
        health={health}
        scanning={scanning}
        onScanDemo={() => handleScan(scanDemo)}
        onScanPath={(path) => handleScan(() => scanPath(path))}
      />

      <div className="relative">
        {graph ? (
          <GraphCanvas
            graph={graph}
            highlightedNodeIds={revealedIds}
            targetNodeId={result?.resolved_node || null}
            riskLevel={result?.report?.risk_level || null}
            highlightedEdgeIds={highlightedEdgeIds}
          />
        ) : (
          <div className="h-full flex items-center justify-center text-muted text-sm">
            {scanning ? "Building the architecture map…" : "Scan a repository to begin."}
          </div>
        )}
        {error && (
          <div className="absolute top-4 left-1/2 -translate-x-1/2 text-sm bg-risk-critical/15 text-risk-critical border border-risk-critical/40 rounded-md px-3 py-1.5">
            {error}
          </div>
        )}
      </div>

      <InvestigationPanel
        disabled={!sessionId}
        investigating={investigating}
        result={result}
        onAsk={handleAsk}
      />
    </main>
  );
}
