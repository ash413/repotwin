export type NodeType =
  | "module"
  | "service"
  | "database"
  | "cache"
  | "queue"
  | "external_api";

export interface GraphNode {
  id: string;
  type: NodeType;
  label: string;
  color: string;
  file: string | null;
  route_count: number;
  model_count: number;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  evidence_count: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface ScanResponse {
  session_id: string;
  graph: GraphData;
}

export interface AffectedModule {
  node_id: string;
  label: string;
  distance: number;
  evidence: { file: string; line: number; snippet: string }[];
}

export interface ImpactReport {
  target: string;
  target_type: string;
  risk_level: "critical" | "high" | "medium" | "low";
  risk_reasons: string[];
  recommendation: string;
  directly_affected: AffectedModule[];
  transitively_affected: AffectedModule[];
  affected_routes: { method: string; path: string | null; function: string; module: string }[];
}

export interface InvestigateResponse {
  question: string;
  extracted_entity?: string;
  resolved_node?: string;
  narrative?: string;
  narrative_source?: "gpt-5.6" | "deterministic";
  report?: ImpactReport;
  error?: string;
}

export interface HealthReport {
  circular_dependencies: string[][];
  high_coupling_modules: { module: string; degree: number }[];
  single_points_of_failure: { node: string; type: string; dependents: number }[];
  orphaned_modules: string[];
  risky_files: { module: string; infra_touched: string[] }[];
  summary: {
    total_modules: number;
    total_infra_components: number;
    cycle_count: number;
    spof_count: number;
  };
}
