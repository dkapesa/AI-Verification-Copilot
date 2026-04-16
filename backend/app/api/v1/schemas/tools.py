from __future__ import annotations

from pydantic import BaseModel


class RunToolsRequest(BaseModel):
    tool_names: list[str] | None = None


class ToolResultResponse(BaseModel):
    tool_name: str
    status: str
    score: float | None
    confidence: float | None
    summary: str | None


class RunToolsResponse(BaseModel):
    case_id: str
    results: list[ToolResultResponse]