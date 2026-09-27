// API client. Wraps fetch with bearer-token injection and typed responses.

const API_BASE_URL =
  (import.meta as any).env?.VITE_API_BASE_URL ?? "http://localhost:8000";

let accessToken: string | null = null;
let onUnauthorized: (() => void) | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function setUnauthorizedHandler(handler: () => void) {
  onUnauthorized = handler;
}

async function request<T>(
  path: string,
  init: RequestInit & { json?: any } = {}
): Promise<T> {
  const headers = new Headers(init.headers || {});
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  let body = init.body;
  if (init.json !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(init.json);
  }
  const res = await fetch(`${API_BASE_URL}/api/v1${path}`, {
    ...init,
    headers,
    body,
  });
  if (res.status === 401 && onUnauthorized) {
    onUnauthorized();
  }
  if (!res.ok) {
    let detail: any;
    try {
      detail = await res.json();
    } catch {
      detail = await res.text();
    }
    const err = new Error(
      typeof detail === "string" ? detail : detail?.detail ?? res.statusText
    ) as Error & { status?: number; detail?: any };
    err.status = res.status;
    err.detail = detail;
    throw err;
  }
  if (res.status === 204) return undefined as unknown as T;
  return (await res.json()) as T;
}

export const api = {
  // Auth
  login: (email: string, password: string) =>
    request<{ access_token: string; refresh_token: string; expires_in: number }>(
      "/auth/login",
      { method: "POST", json: { email, password } }
    ),
  me: () => request<import("@/types/api").User>("/auth/me"),

  // Patients
  listPatients: () =>
    request<{
      items: import("@/types/api").PatientSummary[];
      total: number;
    }>("/patients"),
  getPatient: (id: string) =>
    request<import("@/types/api").PatientDetail>(`/patients/${id}`),

  // Cases
  listCases: () =>
    request<import("@/types/api").CaseListItem[]>("/cases"),
  getCase: (id: string) =>
    request<import("@/types/api").CaseResponse>(`/cases/${id}`),
  createCase: (payload: {
    patient_id: string;
    decision_class: string;
    title: string;
    senior_reviewer_id?: string | null;
  }) =>
    request<import("@/types/api").CaseResponse>("/cases", {
      method: "POST",
      json: payload,
    }),

  // Decision classes
  listDecisionClasses: () =>
    request<import("@/types/api").DecisionClass[]>("/decision-classes"),

  // Recommendations
  listCaseRecommendations: (caseId: string) =>
    request<import("@/types/api").RecommendationListItem[]>(
      `/cases/${caseId}/recommendations`
    ),
  createRecommendation: (caseId: string) =>
    request<import("@/types/api").RecommendationResponse>(
      `/cases/${caseId}/recommendations`,
      { method: "POST" }
    ),
  getRecommendation: (id: string) =>
    request<import("@/types/api").RecommendationResponse>(
      `/recommendations/${id}`
    ),
  acceptRecommendation: (id: string) =>
    request<import("@/types/api").ActionResponse>(
      `/recommendations/${id}/accept`,
      { method: "POST" }
    ),
  requestEvidence: (id: string) =>
    request<{
      recommendation_id: string;
      state: string;
      snapshot_sequence: number;
    }>(`/recommendations/${id}/request-evidence`, { method: "POST" }),
  escalateRecommendation: (id: string, note?: string) =>
    request<import("@/types/api").ActionResponse>(
      `/recommendations/${id}/escalate`,
      { method: "POST", json: { note } }
    ),
  overrideRecommendation: (id: string, rationale: string) =>
    request<import("@/types/api").ActionResponse>(
      `/recommendations/${id}/override`,
      { method: "POST", json: { rationale } }
    ),
  elicitResponse: (
    id: string,
    selected_option_id: string,
    free_text_response?: string
  ) =>
    request<import("@/types/api").ActionResponse>(
      `/recommendations/${id}/elicit`,
      { method: "POST", json: { selected_option_id, free_text_response } }
    ),

  // Reviewer
  reviewQueue: () =>
    request<import("@/types/api").RecommendationListItem[]>("/review/queue"),
  resolveRecommendation: (
    id: string,
    final_recommendation_text: string,
    rationale: string
  ) =>
    request<import("@/types/api").RecommendationResponse>(
      `/review/${id}/resolve`,
      { method: "POST", json: { final_recommendation_text, rationale } }
    ),

  // Admin / audit
  listUsers: () =>
    request<
      Array<{
        id: string;
        email: string;
        full_name: string;
        roles: string[];
        is_active: boolean;
        last_login_at: string | null;
        created_at: string;
      }>
    >("/users"),
  listAuditEvents: (params: Record<string, string | number | undefined> = {}) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") qs.set(k, String(v));
    });
    const q = qs.toString();
    return request<import("@/types/api").AuditEvent[]>(
      `/audit/events${q ? "?" + q : ""}`
    );
  },
  listModelVersions: () =>
    request<import("@/types/api").ModelVersionUsage[]>(
      "/audit/model-versions"
    ),
  auditCsvUrl: (params: Record<string, string | undefined> = {}) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v) qs.set(k, v);
    });
    const tokenQS = accessToken
      ? `&access_token=${encodeURIComponent(accessToken)}`
      : "";
    return `${API_BASE_URL}/api/v1/audit/events/export.csv?${qs}${tokenQS}`;
  },
};
