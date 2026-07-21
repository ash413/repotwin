"""AST-based extraction of structure and evidence from Python source files.

For each file we extract:
- imports (module-level dependency edges)
- top-level functions/classes with line ranges
- FastAPI/Flask route decorators (API surface)
- SQLAlchemy model class definitions (__tablename__)
- "infra signals": evidence that a file talks to Redis, Postgres/SQLAlchemy,
  Stripe, or Celery, with the exact line number of the call site.
"""

import ast
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional


# module-name -> infra category, used to flag import-level evidence
INFRA_IMPORT_SIGNALS = {
    "redis": "redis",
    "celery": "celery",
    "stripe": "stripe",
    "sqlalchemy": "postgres",
    "psycopg2": "postgres",
}

# attribute/call name substrings -> infra category, used to flag call-site evidence
INFRA_CALL_SIGNALS = {
    "redis": "redis",
    "setex": "redis",
    "zadd": "redis",
    "zremrangebyscore": "redis",
    "zcard": "redis",
    ".delay(": "celery",
    "celery": "celery",
    "stripe.": "stripe",
    "PaymentIntent": "stripe",
    "query(": "postgres",
    "SessionLocal": "postgres",
}


@dataclass
class Evidence:
    file: str
    line: int
    snippet: str
    category: str


@dataclass
class FileAnalysis:
    file: str
    imports: List[str] = field(default_factory=list)
    from_imports: List[str] = field(default_factory=list)  # "module:name"
    functions: List[Dict] = field(default_factory=list)
    classes: List[Dict] = field(default_factory=list)
    routes: List[Dict] = field(default_factory=list)
    models: List[Dict] = field(default_factory=list)
    infra_evidence: List[Evidence] = field(default_factory=list)


ROUTE_DECORATOR_METHODS = {"get", "post", "put", "delete", "patch"}


def _decorator_route_info(dec: ast.expr) -> Optional[Dict]:
    """Detect @router.get('/x') / @app.post('/x') style decorators."""
    if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
        method = dec.func.attr
        if method in ROUTE_DECORATOR_METHODS:
            path = None
            if dec.args and isinstance(dec.args[0], ast.Constant):
                path = dec.args[0].value
            return {"method": method.upper(), "path": path}
    return None


def analyze_file(root: str, rel_path: str) -> FileAnalysis:
    full_path = os.path.join(root, rel_path)
    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
        source = f.read()

    analysis = FileAnalysis(file=rel_path)

    try:
        tree = ast.parse(source, filename=rel_path)
    except SyntaxError:
        return analysis

    lines = source.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                analysis.imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for alias in node.names:
                analysis.from_imports.append(f"{mod}:{alias.name}")

        elif isinstance(node, ast.FunctionDef):
            route_info = None
            for dec in node.decorator_list:
                info = _decorator_route_info(dec)
                if info:
                    route_info = info
                    break
            entry = {"name": node.name, "line": node.lineno, "end_line": getattr(node, "end_lineno", node.lineno)}
            analysis.functions.append(entry)
            if route_info:
                analysis.routes.append({**route_info, "function": node.name, "line": node.lineno})

        elif isinstance(node, ast.ClassDef):
            analysis.classes.append({
                "name": node.name,
                "line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
            })
            # detect SQLAlchemy models via __tablename__ assignment
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name) and target.id == "__tablename__":
                            if isinstance(item.value, ast.Constant):
                                analysis.models.append({
                                    "class": node.name,
                                    "table": item.value.value,
                                    "line": node.lineno,
                                })

    # Import-level infra evidence
    for imp in analysis.imports + [f.split(":")[0] for f in analysis.from_imports]:
        base = imp.split(".")[0]
        if base in INFRA_IMPORT_SIGNALS:
            category = INFRA_IMPORT_SIGNALS[base]
            analysis.infra_evidence.append(
                Evidence(file=rel_path, line=1, snippet=f"import {imp}", category=category)
            )

    # Call-site infra evidence (line-level, textual scan for speed + line numbers)
    for i, line in enumerate(lines, start=1):
        for signal, category in INFRA_CALL_SIGNALS.items():
            if signal in line:
                analysis.infra_evidence.append(
                    Evidence(file=rel_path, line=i, snippet=line.strip()[:120], category=category)
                )

    return analysis


def analyze_repo(root: str, python_files: List[str]) -> List[FileAnalysis]:
    results = []
    for rel_path in python_files:
        try:
            results.append(analyze_file(root, rel_path))
        except Exception:
            # Don't let one bad file break the whole scan
            continue
    return results
