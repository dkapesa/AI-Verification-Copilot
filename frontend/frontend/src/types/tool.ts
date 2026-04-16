export interface ToolResult {
  id?: string;
  case_id?: string;
  tool_name: string;
  status: string;
  score: number | null;
  confidence: number | null;
  summary: string;
  signals?: Record<string, unknown> | unknown[];
  output?: Record<string, unknown>;
  error_message?: string | null;
  latency_ms?: number | null;
  started_at?: string;
  completed_at?: string;
}