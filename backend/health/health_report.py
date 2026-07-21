import networkx as nx


def compute_health(g: nx.DiGraph) -> dict:
    module_nodes = [n for n, d in g.nodes(data=True) if d.get("type") == "module"]
    module_subgraph = g.subgraph(module_nodes)

    # Circular dependencies among modules
    cycles = list(nx.simple_cycles(module_subgraph))

    # High-coupling modules: highest in+out degree among modules
    coupling = sorted(
        ((n, g.in_degree(n) + g.out_degree(n)) for n in module_nodes),
        key=lambda kv: kv[1], reverse=True,
    )
    high_coupling = [{"module": n, "degree": d} for n, d in coupling[:5] if d > 0]

    # Single points of failure: infra nodes with no same-type alternative and >=1 dependents
    infra_nodes = [(n, d) for n, d in g.nodes(data=True) if d.get("type") in ("database", "cache", "queue")]
    type_counts = {}
    for n, d in infra_nodes:
        type_counts[d["type"]] = type_counts.get(d["type"], 0) + 1
    spofs = []
    for n, d in infra_nodes:
        dependents = g.in_degree(n) if g.has_node(n) else 0
        if type_counts[d["type"]] == 1 and dependents > 0:
            spofs.append({"node": n, "type": d["type"], "dependents": dependents})

    # Orphaned modules: no incoming or outgoing edges at all
    orphans = [n for n in module_nodes if g.in_degree(n) == 0 and g.out_degree(n) == 0]

    # Risky files: modules that touch >=2 distinct infra categories directly
    risky_files = []
    for n in module_nodes:
        infra_targets = {
            g.nodes[t].get("type") for t in g.successors(n)
            if g.nodes[t].get("type") in ("database", "cache", "queue", "external_api")
        }
        if len(infra_targets) >= 2:
            risky_files.append({"module": n, "infra_touched": sorted(infra_targets)})

    return {
        "circular_dependencies": [list(c) for c in cycles],
        "high_coupling_modules": high_coupling,
        "single_points_of_failure": spofs,
        "orphaned_modules": orphans,
        "risky_files": risky_files,
        "summary": {
            "total_modules": len(module_nodes),
            "total_infra_components": len(infra_nodes),
            "cycle_count": len(cycles),
            "spof_count": len(spofs),
        },
    }
