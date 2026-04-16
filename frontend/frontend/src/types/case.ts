export type CaseStatus =
  | "PENDING"
  | "APPROVED"
  | "ESCALATED"
  | "REJECTED"
  | string;

export interface CaseSummary {
  id: string;
  user_id: string;
  email: string;
  status: CaseStatus;
  created_at: string;
  updated_at: string;
}

export interface CaseDetail extends CaseSummary {
  device_info: Record<string, unknown>;
  document_check_result: Record<string, unknown>;
  behaviour_summary: Record<string, unknown>;
}

export interface CaseListResponse {
  items: CaseSummary[];
  total: number;
  limit: number;
  offset: number;
}