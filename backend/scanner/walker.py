"""Walks a repository and classifies files for downstream analysis."""

import os

IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", ".pytest_cache", "site-packages",
}

CONFIG_FILENAMES = {
    "docker-compose.yml", "docker-compose.yaml", "Dockerfile",
    "requirements.txt", "pyproject.toml", "package.json",
    ".env", ".env.example", "Procfile",
}


def walk_repo(root: str):
    """Returns a dict with categorized file lists (all paths relative to root)."""
    python_files = []
    config_files = []
    other_files = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for fname in filenames:
            full = os.path.join(dirpath, fname)
            rel = os.path.relpath(full, root)

            if fname in CONFIG_FILENAMES:
                config_files.append(rel)
            elif fname.endswith(".py"):
                python_files.append(rel)
            else:
                other_files.append(rel)

    return {
        "root": root,
        "python_files": sorted(python_files),
        "config_files": sorted(config_files),
        "other_files": sorted(other_files),
    }
