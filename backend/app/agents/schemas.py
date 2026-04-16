# backend/app/agents/schemas.py
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class AggregatedSignal(BaseModel):
    overall_risk_score: float = Field(ge=0.0, le=1.0, default=0.0)
    high_risk_flags: list[str] = Field(default_factory=list)
    moderate_risk_flags: list[str] = Field(default_factory=list)
    low_risk_flags: list[str] = Field(default_factory=list)
    tool_summaries: list[dict[str, Any]] = Field(default_factory=list)
    tools_failed: list[str] = Field(default_factory=list)


class DecisionOutput(BaseModel):
    decision: Literal["APPROVE", "ESCALATE", "REJECT"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list, min_length=1)
    recommended_next_steps: list[str] = Field(default_factory=list)


class AIReviewResponse(BaseModel):
    case_id: str
    status: Literal["COMPLETED", "FAILED"]
    decision: DecisionOutput | None = None
    aggregated_signals: AggregatedSignal | None = None
    tool_results_count: int = 0
    errors: list[str] = Field(default_factory=list)