from scanner.walker import walk_repo
from scanner.python_analyzer import analyze_repo
from scanner.config_analyzer import analyze_configs
from scanner.graph_builder import build_graph


def scan_repository(root: str):
    """Runs the full scan pipeline and returns a NetworkX graph plus raw scan data."""
    walked = walk_repo(root)
    file_analyses = analyze_repo(root, walked["python_files"])
    config_analysis = analyze_configs(root, walked["config_files"])
    graph = build_graph(root, file_analyses, config_analysis)
    return {
        "graph": graph,
        "walked": walked,
        "file_analyses": file_analyses,
        "config_analysis": config_analysis,
    }
