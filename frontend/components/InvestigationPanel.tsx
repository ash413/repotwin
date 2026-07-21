"use client";

import { useState } from "react";
import { InvestigateResponse } from "@/lib/types";

const SUGGESTIONS = [
  "What breaks if I remove Redis?",
  "What depends on the users table?",
  "Where could this application fail if Stripe goes down?",
];

const RISK_STYLES: Record<string, string> = {
  critical: "bg-risk-critical/15 text-risk-critical border-risk-critical/40",
  high: "bg-risk-high/15 text-risk-high border-risk-high/40",
  medium: "bg-risk-medium/15 text-risk-medium border-risk-medium/40",
  low: "bg-risk-low/15 text-risk-low border-risk-low/40",
};

interface InvestigationPanelProps {
  disabled: boolean;
  investigating: boolean;
  result: InvestigateResponse | null;
  onAsk: (question: string) => void;
}

export default function InvestigationPanel({
  disabled,
  investigating,
  result,
  onAsk,
}: InvestigationPanelProps) {
  const [question, setQuestion] = useState("");

  const submit = () => {
    if (question.trim()) onAsk(question.trim());
  };

  return (
    <div className="h-full flex flex-col bg-surface border-l border-border">
      <div className="p-4 border-b border-border">
        <div className="text-xs uppercase tracking-wider text-muted mb-1">Investigation</div>
        <div className="text-lg font-semibold text-text">Ask about a change</div>
      </div>

      <div className="p-4 border-b border-border space-y-2">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          disabled={disabled}
          placeholder="What breaks if I remove Redis?"
          rows={2}
          className="w-full bg-canvas border border-border rounded-md px-3 py-2 text-sm text-text placeholder:text-muted focus:outline-none focus:border-accent/60 resize-none disabled:opacity-50"
        />
        <button
          onClick={submit}
          disabled={disabled || investigating || !question.trim()}
          className="w-full text-sm font-medium bg-accent/15 text-accent border border-accent/40 rounded-md py-2 hover:bg-accent/25 transition-colors disabled:opacity-40"
        >
          {investigating ? "Investigating…" : "Investigate"}
        </button>
        <div className="flex flex-wrap gap-1.5 pt-1">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              disabled={disabled}
              onClick={() => {
                setQuestion(s);
                onAsk(s);
              }}
              className="text-[11px] text-muted border border-border rounded-full px-2.5 py-1 hover:text-text hover:border-accent/40 disabled:opacity-40"
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {!result && (
          <div className="text-sm text-muted leading-relaxed">
            Ask a question about removing, changing, or replacing a
            component. RepoTwin traces the real dependency graph and shows
            you the evidence — not a guess.
          </div>
        )}

        {result?.error && (
          <div className="text-sm text-risk-high bg-risk-high/10 border border-risk-high/30 rounded-md p-3">
            {result.error}
          </div>
        )}

        {result?.report && (
          <>
            <div className="flex items-center gap-2">
              <span
                className={`text-xs font-mono uppercase tracking-wide border rounded-full px-2.5 py-1 ${
                  RISK_STYLES[result.report.risk_level]
                }`}
              >
                {result.report.risk_level} risk
              </span>
              <span className="text-xs text-muted font-mono">{result.resolved_node}</span>
            </div>

            {result.narrative && (
              <div className="text-sm text-text/90 leading-relaxed whitespace-pre-line">
                {result.narrative}
              </div>
            )}

            {result.report.affected_routes.length > 0 && (
              <Section title="Affected API routes">
                <div className="space-y-1">
                  {result.report.affected_routes.map((r, i) => (
                    <div
                      key={i}
                      className="text-xs font-mono bg-canvas border border-border rounded px-2 py-1 flex gap-2"
                    >
                      <span className="text-accent">{r.method}</span>
                      <span className="text-text/80">{r.path || "(unknown path)"}</span>
                    </div>
                  ))}
                </div>
              </Section>
            )}

            <Section
              title={`Directly affected (${result.report.directly_affected.length})`}
            >
              <div className="space-y-2">
                {result.report.directly_affected.map((m) => (
                  <div key={m.node_id} className="border border-border rounded-md p-2 bg-canvas">
                    <div className="text-sm text-text/90 font-medium">{m.label}</div>
                    {m.evidence.slice(0, 2).map((ev, i) => (
                      <div key={i} className="text-[11px] font-mono text-muted mt-1 truncate">
                        {ev.file}:{ev.line} — {ev.snippet}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </Section>

            {result.report.transitively_affected.length > 0 && (
              <Section
                title={`Transitively affected (${result.report.transitively_affected.length})`}
              >
                <div className="flex flex-wrap gap-1.5">
                  {result.report.transitively_affected.map((m) => (
                    <span
                      key={m.node_id}
                      className="text-[11px] font-mono text-muted border border-border rounded px-2 py-1"
                    >
                      {m.label}
                    </span>
                  ))}
                </div>
              </Section>
            )}

            <Section title="Recommended migration plan">
              <div className="text-sm text-text/90 leading-relaxed bg-canvas border border-border rounded-md p-3">
                {result.report.recommendation}
              </div>
            </Section>
          </>
        )}
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wider text-muted mb-2">{title}</div>
      {children}
    </div>
  );
}
