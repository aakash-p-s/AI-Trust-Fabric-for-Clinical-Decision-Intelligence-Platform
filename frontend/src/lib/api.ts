import type {
  ChangelogEntry,
  ComplianceRulebook,
  DashboardSummary,
  DigitalTwin,
  DigitalTwinDetail,
  DriftAlert,
  TrustMonitoringSummary,
  TwinListResponse,
  User,
} from "./types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function authHeaders(role?: string): Record<string, string> {
  return role ? { "X-User-Role": role } : {};
}

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || body.error || detail;
    } catch {
      /* no JSON body */
    }
    throw new Error(detail);
  }
  return response.json();
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------
export async function login(
  username: string,
  password: string
): Promise<{ success: boolean; user?: User; error?: string }> {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  return res.json();
}

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------
export async function getDashboardSummary(): Promise<DashboardSummary> {
  const res = await fetch(`${API_URL}/dashboard/summary`);
  return handle(res);
}

// ---------------------------------------------------------------------------
// Twins
// ---------------------------------------------------------------------------
export interface TwinListParams {
  status?: "all" | "cleared" | "flagged";
  model_version?: string;
  search?: string;
  sort_by?: "confidence" | "twin_created_at";
  sort_dir?: "asc" | "desc";
  page?: number;
  limit?: number;
}

export async function listTwins(params: TwinListParams = {}): Promise<TwinListResponse> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== "") query.set(k, String(v));
  });
  const res = await fetch(`${API_URL}/twins?${query.toString()}`);
  return handle(res);
}

export async function getTwin(twinId: string): Promise<DigitalTwinDetail> {
  const res = await fetch(`${API_URL}/twins/${twinId}`);
  return handle(res);
}

export async function reviewTwin(
  twinId: string,
  reviewerUsername: string,
  decision: "approve" | "override",
  notes: string,
  role: string
): Promise<DigitalTwin> {
  const res = await fetch(`${API_URL}/twins/${twinId}/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(role) },
    body: JSON.stringify({ reviewer_username: reviewerUsername, decision, notes }),
  });
  return handle(res);
}

// ---------------------------------------------------------------------------
// Rulebook
// ---------------------------------------------------------------------------
export async function getRulebook(): Promise<ComplianceRulebook> {
  const res = await fetch(`${API_URL}/rulebook`);
  return handle(res);
}

export async function updateRulebook(
  rulebook: ComplianceRulebook,
  changedBy: string,
  role: string
): Promise<{ success: boolean; rulebook: ComplianceRulebook }> {
  const res = await fetch(`${API_URL}/rulebook`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...authHeaders(role) },
    body: JSON.stringify({ ...rulebook, changed_by: changedBy }),
  });
  return handle(res);
}

export async function getRulebookChangelog(limit = 20): Promise<{ entries: ChangelogEntry[] }> {
  const res = await fetch(`${API_URL}/rulebook/changelog?limit=${limit}`);
  return handle(res);
}

// ---------------------------------------------------------------------------
// Trust monitoring
// ---------------------------------------------------------------------------
export async function getTrustMonitoringSummary(
  modelVersion?: string
): Promise<TrustMonitoringSummary> {
  const query = modelVersion ? `?model_version=${encodeURIComponent(modelVersion)}` : "";
  const res = await fetch(`${API_URL}/trust-monitoring/summary${query}`);
  return handle(res);
}

export async function runTrustCheckNow(
  modelVersion?: string
): Promise<TrustMonitoringSummary & { new_alerts: DriftAlert[] }> {
  const query = modelVersion ? `?model_version=${encodeURIComponent(modelVersion)}` : "";
  const res = await fetch(`${API_URL}/trust-monitoring/run-now${query}`, { method: "POST" });
  return handle(res);
}

export async function getDriftAlerts(limit = 20): Promise<{ alerts: DriftAlert[] }> {
  const res = await fetch(`${API_URL}/trust-monitoring/alerts?limit=${limit}`);
  return handle(res);
}
