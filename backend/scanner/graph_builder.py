"""Fuses python_analyzer + config_analyzer output into one NetworkX graph.

Node types: module, api_route_group, database, cache, queue, external_api
Edge types: imports, reads_writes, calls, deploys_with
"""

import os
import networkx as nx


def module_id_for_file(rel_path: str) -> str:
    """Turn a file path like app/services/cache.py into a module id app.services.cache"""
    no_ext = rel_path[:-3] if rel_path.endswith(".py") else rel_path
    return no_ext.replace(os.sep, ".").replace("/", ".")


def build_graph(root: str, file_analyses, config_analysis) -> nx.DiGraph:
    g = nx.DiGraph()

    # --- module nodes, one per python file ---
    module_ids = {}
    for fa in file_analyses:
        mid = module_id_for_file(fa.file)
        module_ids[fa.file] = mid
        g.add_node(mid, type="module", label=mid.split(".")[-1], file=fa.file,
                   functions=fa.functions, classes=fa.classes, routes=fa.routes,
                   models=fa.models)

    # --- infra nodes from config (docker-compose services, packages) ---
    for svc in config_analysis.compose_services:
        if not g.has_node(svc["node_id"]):
            g.add_node(svc["node_id"], type=svc["node_type"], label=svc["label"], source="compose")
    for pkg in config_analysis.packages:
        if not g.has_node(pkg["node_id"]):
            g.add_node(pkg["node_id"], type=pkg["node_type"], label=pkg["label"], source="requirements")

    # --- import edges between modules (module -> module) ---
    file_by_module_suffix = {mid: f for f, mid in module_ids.items()}
    for fa in file_analyses:
        src_mid = module_ids[fa.file]
        all_imports = fa.imports + [fi.split(":")[0] for fi in fa.from_imports]
        for imp in all_imports:
            # try to resolve to a known local module id (suffix match, since imports use dotted names
            # like app.services.cache while our ids are the same format when rooted at repo root)
            for candidate_mid in module_ids.values():
                if candidate_mid == imp or candidate_mid.endswith("." + imp.split(".")[-1]):
                    if candidate_mid != src_mid and imp.startswith("app."):
                        g.add_edge(src_mid, candidate_mid, type="imports")
                    break

    # --- infra evidence edges (module -> infra node), e.g. cache.py -> redis ---
    infra_node_for_category = {}
    for n, data in g.nodes(data=True):
        if data.get("type") in ("database", "cache", "queue", "external_api"):
            infra_node_for_category.setdefault(data["type"], []).append(n)

    # category -> which infra node id it maps to, based on what's declared in compose/requirements
    category_to_node = {}
    for svc in config_analysis.compose_services:
        cat = {"database": "postgres", "cache": "redis", "queue": "queue"}.get(svc["node_type"])
        if svc["node_id"] == "postgres":
            category_to_node["postgres"] = svc["node_id"]
        if svc["node_id"] == "redis":
            category_to_node["redis"] = svc["node_id"]
    for pkg in config_analysis.packages:
        if pkg["node_id"] == "stripe":
            category_to_node["stripe"] = pkg["node_id"]
        if pkg["node_id"] == "celery":
            category_to_node["celery"] = pkg["node_id"]

    for fa in file_analyses:
        src_mid = module_ids[fa.file]
        seen_categories_this_file = set()
        for ev in fa.infra_evidence:
            target_node = category_to_node.get(ev.category)
            if not target_node or not g.has_node(target_node):
                continue
            key = (src_mid, target_node)
            if g.has_edge(*key):
                g[src_mid][target_node]["evidence"].append(
                    {"line": ev.line, "snippet": ev.snippet, "file": ev.file}
                )
            else:
                g.add_edge(src_mid, target_node, type="reads_writes",
                          evidence=[{"line": ev.line, "snippet": ev.snippet, "file": ev.file}])

    return g
