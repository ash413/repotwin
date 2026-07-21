import {
  ScanResponse,
  InvestigateResponse,
  HealthReport,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8420";

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed with status ${res.status}`);
  }
  return res.json();
}

export async function scanDemo(): Promise<ScanResponse> {
  const res = await fetch(`${API_BASE}/scan/demo`, { method: "POST" });
  return handle<ScanResponse>(res);
}

export async function scanPath(path: string): Promise<ScanResponse> {
  const res = await fetch(`${API_BASE}/scan/path`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path }),
  });
  return handle<ScanResponse>(res);
}

export async function scanUpload(file: File): Promise<ScanResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/scan/upload`, { method: "POST", body: form });
  return handle<ScanResponse>(res);
}

export async function investigate(
  sessionId: string,
  question: string
): Promise<InvestigateResponse> {
  const res = await fetch(`${API_BASE}/investigate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, question }),
  });
  return handle<InvestigateResponse>(res);
}

export async function getHealthReport(sessionId: string): Promise<HealthReport> {
  const res = await fetch(`${API_BASE}/health-report/${sessionId}`);
  return handle<HealthReport>(res);
}
