# backend/app/agents/state.py
from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.agents.schemas import AggregatedSignal, DecisionOutput


class AgentState(BaseModel):
    case_id: UUID
    case_data: dict[str, Any] | None = None

    requested_tools: list[str] = Field(default_factory=list)
    tool_outputs: list[dict[str, Any]] = Field(default_factory=list)
    aggregated_signals: AggregatedSignal | None = None
    decision: DecisionOutput | None = None

    reasoning_summary: str | None = None
    errors: list[str] = Field(default_factory=list)
    retry_count: int = 0

    model_provider: str | None = None
    model_name: str | None = None
    prompt_version: str = "v1"

    started_at_ms: int | None = None
    completed_at_ms: int | None = None
    latency_ms: int | None = None