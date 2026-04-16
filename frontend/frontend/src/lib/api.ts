import { API_BASE_URL } from "./config";
import type { CaseDetail, CaseListResponse } from "@/types/case";

export class APIError extends Error {
  status: number;
  body: string;

  constructor(status: number, body: string) {
    super(`API error ${status}: ${body}`);
    this.name = "APIError";
    this.status = status;
    this.body = body;
  }
}

export type ToolResult = {
  tool_name: string;
  status: string;
  score: number | null;
  confidence: number | null;
  summary: string | null;
};

export type ToolRunsResponse = {
  case_id: string;
  results: ToolResult[];
};

export type AuditLogEvent = {
  id: string;
  case_id: string | null;
  event_type: string;
  actor_type: string | null;
  subject: string | null;
  latency_ms: number | null;
  meta: Record<string, unknown> | null;
  created_at: string;
};

export type OverrideDecision = "APPROVE" | "ESCALATE" | "REJECT";

export type HumanOverrideRequest = {
  decision: OverrideDecision;
  note: string;
};

async function apiRequest(path: string, init?: RequestInit): Promise<Response> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const text = await response.text();
    throw new APIError(response.status, text);
  }

  return response;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await apiRequest(path, init);
  return response.json() as Promise<T>;
}

export function getCases(limit = 20, offset = 0) {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });

  return apiFetch<CaseListResponse>(`/api/v1/cases?${params.toString()}`);
}

export function getCase(caseId: string) {
  return apiFetch<CaseDetail>(`/api/v1/cases/${encodeURIComponent(caseId)}`);
}

export function getCaseToolRuns(caseId: string) {
  return apiFetch<ToolRunsResponse>(
    `/api/v1/cases/${encodeURIComponent(caseId)}/tool-runs`
  );
}

export function runCaseTools(caseId: string) {
  return apiFetch<ToolRunsResponse>(
    `/api/v1/cases/${encodeURIComponent(caseId)}/run-tools`,
    {
      method: "POST",
      body: JSON.stringify({}),
    }
  );
}

export function getLatestAIReview(caseId: string) {
  return apiFetch<unknown>(
    `/api/v1/cases/${encodeURIComponent(caseId)}/ai-reviews/latest`
  );
}

export function runCaseAIReview(caseId: string) {
  return apiFetch<unknown>(
    `/api/v1/cases/${encodeURIComponent(caseId)}/ai-review`,
    {
      method: "POST",
    }
  );
}

export function getCaseAuditLogs(caseId: string) {
  return apiFetch<AuditLogEvent[]>(
    `/api/v1/cases/${encodeURIComponent(caseId)}/audit-logs`
  );
}

export async function submitHumanOverride(
  caseId: string,
  payload: HumanOverrideRequest
) {
  const response = await apiRequest(
    `/api/v1/cases/${encodeURIComponent(caseId)}/human-override`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );

  const contentType = response.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    return response.json();
  }

  const text = await response.text();
  return text;
}