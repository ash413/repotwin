"""Given a target node (e.g. 'redis'), find everything upstream that depends
on it, collect the file/line evidence for each dependency, and score risk.
"""

import networkx as nx
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class AffectedModule:
    node_id: str
    label: str
    distance: int  # hops from the target (1 = direct dependency)
    evidence: List[Dict] = field(default_factory=list)
    routes: List[Dict] = field(default_factory=list)


@dataclass
class ImpactReport:
    target: str
    target_type: str
    directly_affected: List[AffectedModule]
    transitively_affected: List[AffectedModule]
    affected_routes: List[Dict]
    risk_level: str
    risk_reasons: List[str]
    recommendation: str


def find_node(g: nx.DiGraph, query: str) -> Optional[str]:
    """Resolve a free-text entity name (e.g. 'Redis', 'the users table') to a node id."""
    q = query.lower().strip()

    # direct id / label match
    for n, d in g.nodes(data=True):
        if n.lower() == q or d.get("label", "").lower() == q:
            return n

    # substring match against id/label
    for n, d in g.nodes(data=True):
        if q in n.lower() or q in d.get("label", "").lower():
            return n

    # table name match (for "users table" style queries)
    for n, d in g.nodes(data=True):
        for model in d.get("models", []) or []:
            if model["table"].lower() in q or q in model["table"].lower():
                return n

    return None


def analyze_impact(g: nx.DiGraph, target_node: str) -> ImpactReport:
    if not g.has_node(target_node):
        raise ValueError(f"Unknown node: {target_node}")

    target_data = g.nodes[target_node]
    # Everything with a path TO the target (i.e. depends on it) via reverse BFS
    reverse_g = g.reverse(copy=False)
    lengths = nx.single_source_shortest_path_length(reverse_g, target_node)
    lengths.pop(target_node, None)  # exclude the target itself

    direct = []
    transitive = []
    affected_routes = []

    for node_id, distance in sorted(lengths.items(), key=lambda kv: kv[1]):
        data = g.nodes[node_id]
        evidence = []
        # collect edge evidence along any direct edge from this node to the target
        if g.has_edge(node_id, target_node):
            evidence = g[node_id][target_node].get("evidence", [])

        routes = data.get("routes", []) or []
        for r in routes:
            affected_routes.append({**r, "module": node_id})

        module = AffectedModule(
            node_id=node_id,
            label=data.get("label", node_id),
            distance=distance,
            evidence=evidence,
            routes=routes,
        )
        if distance == 1:
            direct.append(module)
        else:
            transitive.append(module)

    risk_level, risk_reasons = _score_risk(g, target_node, direct, transitive, affected_routes)
    recommendation = _build_recommendation(target_data, direct, transitive, risk_level)

    return ImpactReport(
        target=target_node,
        target_type=target_data.get("type", "unknown"),
        directly_affected=direct,
        transitively_affected=transitive,
        affected_routes=affected_routes,
        risk_level=risk_level,
        risk_reasons=risk_reasons,
        recommendation=recommendation,
    )


def _score_risk(g, target_node, direct, transitive, affected_routes):
    reasons = []
    score = 0

    total_affected = len(direct) + len(transitive)
    if total_affected >= 6:
        score += 2
        reasons.append(f"{total_affected} modules transitively depend on this component")
    elif total_affected >= 3:
        score += 1
        reasons.append(f"{total_affected} modules depend on this component")

    if affected_routes:
        score += 1
        reasons.append(f"{len(affected_routes)} API route(s) become affected")

    node_type = g.nodes[target_node].get("type")
    if node_type in ("database", "cache", "queue"):
        score += 1
        reasons.append(f"'{target_node}' is core infrastructure ({node_type})")

    # single point of failure: nothing else in the graph provides the same node_type
    same_type_alternatives = [
        n for n, d in g.nodes(data=True)
        if d.get("type") == node_type and n != target_node
    ]
    if node_type in ("database", "cache", "queue") and not same_type_alternatives:
        score += 1
        reasons.append("no redundant/alternative component of the same type exists in this repo")

    if score >= 4:
        level = "critical"
    elif score >= 2:
        level = "high"
    elif score >= 1:
        level = "medium"
    else:
        level = "low"

    return level, reasons


def _build_recommendation(target_data, direct, transitive, risk_level):
    label = target_data.get("label", "this component")
    node_type = target_data.get("type")

    if node_type == "cache":
        return (
            f"Before removing {label}: (1) identify which of the {len(direct)} directly-dependent "
            f"modules use it for correctness (e.g. session/auth state) vs. pure performance "
            f"(e.g. read-through caching); (2) for correctness-critical paths, migrate state to the "
            f"primary database or a durable store first; (3) add a feature flag to disable "
            f"{label}-backed paths independently so each can be cut over and verified before full removal."
        )
    if node_type == "database":
        return (
            f"Before replacing {label}: (1) freeze schema changes; (2) write a data-migration script "
            f"covering every model/table touched by the {len(direct) + len(transitive)} affected modules; "
            f"(3) run both databases in parallel (dual-write or CDC) during cutover; "
            f"(4) migrate read paths module-by-module, verifying each against the affected routes."
        )
    if node_type == "queue":
        return (
            f"Before removing {label}: (1) inventory all background jobs currently dispatched through it; "
            f"(2) decide which need a synchronous replacement vs. can be deferred safely; "
            f"(3) stand up the new queue in parallel and migrate producers before consumers."
        )
    if node_type == "external_api":
        return (
            f"Before removing {label}: (1) add a circuit breaker / fallback path for the "
            f"{len(direct) + len(transitive)} affected modules so a provider outage degrades gracefully "
            f"instead of failing the request; (2) confirm no business-critical flow silently depends on it."
        )
    return f"Review the {len(direct) + len(transitive)} affected modules individually before proceeding."
