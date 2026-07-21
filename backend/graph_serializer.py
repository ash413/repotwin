"""Converts a NetworkX DiGraph into plain JSON structures for the frontend
(React Flow nodes/edges), stripping non-serializable dataclass fields.
"""

import networkx as nx

NODE_TYPE_COLORS = {
    "module": "#6366f1",
    "service": "#0ea5e9",
    "database": "#16a34a",
    "cache": "#dc2626",
    "queue": "#d97706",
    "external_api": "#9333ea",
}


def serialize_graph(g: nx.DiGraph) -> dict:
    nodes = []
    for n, d in g.nodes(data=True):
        node_type = d.get("type", "module")
        nodes.append({
            "id": n,
            "type": node_type,
            "label": d.get("label", n),
            "color": NODE_TYPE_COLORS.get(node_type, "#6b7280"),
            "file": d.get("file"),
            "route_count": len(d.get("routes") or []),
            "model_count": len(d.get("models") or []),
        })

    edges = []
    for u, v, d in g.edges(data=True):
        edges.append({
            "id": f"{u}->{v}",
            "source": u,
            "target": v,
            "type": d.get("type", "imports"),
            "evidence_count": len(d.get("evidence", [])) if d.get("evidence") else 0,
        })

    return {"nodes": nodes, "edges": edges}
