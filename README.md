# RepoTwin — Software Digital Twin

RepoTwin turns a repository into a living architecture map, then simulates a proposed change against the real dependency graph. Ask “What breaks if Redis goes down?” and RepoTwin highlights the blast radius, affected routes, source evidence, risk level, and a migration plan.

## Why it is different

- **Evidence before AI:** Python AST analysis and configuration parsing build a NetworkX dependency graph. The model never invents the blast radius.
- **GPT-5.6 explanation:** OpenAI GPT-5.6 converts the graph-derived report into a concise engineering brief. If no API key is available, the same analysis still works with a deterministic narrator.
- **Interactive digital twin:** The Next.js/React Flow interface animates affected components and dependency edges while exposing file-and-line evidence.
- **Architecture health:** RepoTwin reports cycles, high-coupling modules, single points of failure, orphans, and files that touch multiple infrastructure layers.

## Architecture

| Layer | What it does |
|---|---|
| `backend/scanner` | Walks Python repos, parses ASTs and config files, and fuses findings into a directed graph |
| `backend/investigator` | Resolves natural-language targets, traverses dependents, scores risk, and builds migration advice |
| `backend/health` | Computes architecture health signals |
| `frontend` | Renders the graph, investigation animation, evidence, and health summary |
| `demo-repo` | Bundled FastAPI target with Redis, PostgreSQL, Stripe, and Celery |

## Run locally

Requirements: Python 3.10+, Node.js 18+, and npm.

```bash
# terminal 1
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8420
```

```bash
# terminal 2
cd frontend
npm ci
npm run dev
```

Open `http://localhost:3000` and choose **Scan demo repository**.

For GPT-5.6 narration, set an API key before starting the backend:

```bash
export OPENAI_API_KEY="your-key"
# Optional; defaults to the explicit hackathon model target.
export OPENAI_MODEL="gpt-5.6-sol"
```

Without `OPENAI_API_KEY`, all graph analysis, risk scoring, visualization, and recommendations remain usable.

## Test

```bash
cd backend
python -m unittest discover -s tests -v
```

```bash
cd frontend
npm ci
npm run build
```

## API

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/scan/demo` | Scan the bundled demo repository |
| `POST` | `/scan/path` | Scan a server-local repository |
| `POST` | `/scan/upload` | Scan an uploaded zip |
| `GET` | `/graph/{session_id}` | Return React Flow-ready graph data |
| `POST` | `/investigate` | Run a change-impact investigation |
| `GET` | `/health-report/{session_id}` | Return the architecture scorecard |

## Built with Codex and GPT-5.6

Codex was used to audit the original prototype against the Build Week judging criteria, migrate the optional third-party narration path to OpenAI’s Responses API, add model provenance to the UI, preserve an offline deterministic fallback, add behavioral tests, and make the project runnable from a single root README. GPT-5.6 is deliberately downstream of deterministic graph analysis: it explains verified evidence instead of guessing repository structure.
