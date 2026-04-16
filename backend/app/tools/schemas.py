from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.tools.types import ToolRunStatus


class ToolCaseInput(BaseModel):
    case_id: UUID
    user_id: str
    email: EmailStr
    device_info: dict[str, Any] = Field(default_factory=dict)
    document_check_result: dict[str, Any] = Field(default_factory=dict)
    behaviour_summary: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    tool_name: str
    status: ToolRunStatus
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    summary: str | None = None
    signals: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    latency_ms: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None