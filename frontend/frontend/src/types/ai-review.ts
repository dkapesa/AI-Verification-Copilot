export type ReviewDecision = "APPROVE" | "ESCALATE" | "REJECT";

export interface ToolSummary {
  tool_name: string;
  status: string;
  score: number;
  confidence: number;
  summary: string;
}

export interface AggregatedSignals {
  overall_risk_score: number;
  high_risk_flags: string[];
  moderate_risk_flags: string[];
  low_risk_flags: string[];
  tool_summaries: ToolSummary[];
  tools_failed?: string[];
}

export interface AIReviewResult {
  id?: string;
  case_id?: string;
  decision: ReviewDecision;
  confidence: number;
  reasons: string[];
  recommended_next_steps: string[];
  aggregated_signals?: AggregatedSignals;
  reasoning_summary?: string | null;
  model_provider?: string | null;
  model_name?: string | null;
  prompt_version?: string | null;
  retry_count?: number | null;
  latency_ms?: number | null;
  created_at?: string;
}