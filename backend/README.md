# RepoTwin — Software Digital Twin

A living, interactive model of a software repository: architecture, dependencies,
data flows, and change-impact simulation. "Google Maps + a simulation engine for software."

## What's in this zip

- `demo-repo/` — a sample FastAPI app (auth + Redis + PostgreSQL + Stripe + Celery)
  used to exercise the scanner. This is a TARGET to scan, not part of the product.
- `backend/` — the actual RepoTwin engine (FastAPI service):
  - `scanner/` — walks a repo, does AST-based Python analysis (imports, routes,
    SQLAlchemy models, infra call-sites) + config parsing (docker-compose.yml,
    requirements.txt, .env), and fuses it all into a NetworkX graph.
  - `investigator/` — natural-language change-impact queries
    ("What breaks if I remove Redis?") via graph traversal + risk scoring.
    Uses Claude for narrative polish if `ANTHROPIC_API_KEY` is set, otherwise a
    template narrative (works with zero external dependencies).
  - `health/` — architecture health scorecard (circular deps, coupling, SPOFs).
  - `main.py` — FastAPI app wiring it all together.
- `frontend/` — not yet built (Next.js + React Flow UI is next).

## Running the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8420
```

In another terminal:

```bash
# Scan the bundled demo repo
curl -X POST http://localhost:8420/scan/demo

# Copy the "session_id" from the response, then:
curl -X POST http://localhost:8420/investigate \
  -H "Content-Type: application/json" \
  -d '{"session_id": "<paste-here>", "question": "What breaks if I remove Redis?"}'

# Architecture health scorecard
curl http://localhost:8420/health-report/<session_id>

# Scan any other repo on disk
curl -X POST http://localhost:8420/scan/path \
  -H "Content-Type: application/json" \
  -d '{"path": "/absolute/path/to/repo"}'

# Or upload a zipped repo
curl -X POST http://localhost:8420/scan/upload -F "file=@myrepo.zip"
```

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | /scan/demo | Scan the bundled demo repo |
| POST | /scan/path | Scan a repo already on disk |
| POST | /scan/upload | Scan an uploaded .zip of a repo |
| GET | /graph/{session_id} | Get the React-Flow-ready graph JSON |
| POST | /investigate | Ask a natural-language impact question |
| GET | /health-report/{session_id} | Architecture health scorecard |

Optional: set `ANTHROPIC_API_KEY` in your environment for LLM-narrated
investigation answers (falls back to template narratives without it).
