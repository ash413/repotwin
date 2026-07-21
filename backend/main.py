import os
import shutil
import tempfile
import uuid
import zipfile

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from scanner import scan_repository
from investigator.nl_query import answer_question
from health.health_report import compute_health
from graph_serializer import serialize_graph

app = FastAPI(title="RepoTwin API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store of scanned repos, keyed by session id.
# Fine for a hackathon MVP; swap for Postgres/SQLite-backed storage for anything real.
SESSIONS: dict = {}

DEMO_REPO_PATH = os.path.join(os.path.dirname(__file__), "..", "demo-repo")


class InvestigateRequest(BaseModel):
    session_id: str
    question: str


class ScanPathRequest(BaseModel):
    path: str


def _run_scan_and_store(root: str) -> str:
    result = scan_repository(root)
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = result
    return session_id


@app.post("/scan/demo")
def scan_demo():
    """Scans the bundled demo repository (auth + Redis + Postgres + Stripe + Celery)."""
    session_id = _run_scan_and_store(DEMO_REPO_PATH)
    return {"session_id": session_id, "graph": serialize_graph(SESSIONS[session_id]["graph"])}


@app.post("/scan/path")
def scan_path(req: ScanPathRequest):
    """Scans a repository already present on disk (e.g. mounted/cloned server-side)."""
    if not os.path.isdir(req.path):
        raise HTTPException(status_code=400, detail=f"Path not found: {req.path}")
    session_id = _run_scan_and_store(req.path)
    return {"session_id": session_id, "graph": serialize_graph(SESSIONS[session_id]["graph"])}


@app.post("/scan/upload")
async def scan_upload(file: UploadFile = File(...)):
    """Accepts a .zip of a repository, extracts it, and scans it."""
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Please upload a .zip archive of the repository")

    tmp_dir = tempfile.mkdtemp(prefix="repotwin_")
    zip_path = os.path.join(tmp_dir, "repo.zip")
    with open(zip_path, "wb") as f:
        f.write(await file.read())

    extract_dir = os.path.join(tmp_dir, "repo")
    os.makedirs(extract_dir, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
    except zipfile.BadZipFile:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail="Invalid zip file")

    session_id = _run_scan_and_store(extract_dir)
    return {"session_id": session_id, "graph": serialize_graph(SESSIONS[session_id]["graph"])}


@app.get("/graph/{session_id}")
def get_graph(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Unknown session_id; scan a repo first")
    return serialize_graph(session["graph"])


@app.post("/investigate")
def investigate(req: InvestigateRequest):
    session = SESSIONS.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Unknown session_id; scan a repo first")
    return answer_question(session["graph"], req.question)


@app.get("/health-report/{session_id}")
def health_report(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Unknown session_id; scan a repo first")
    return compute_health(session["graph"])


@app.get("/health")
def health():
    return {"status": "ok"}
