from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr


class CaseCreate(BaseModel):
    user_id: str
    email: EmailStr
    device_info: dict[str, Any]
    document_check_result: dict[str, Any]
    behaviour_summary: dict[str, Any]


class CaseRead(BaseModel):
    id: UUID
    user_id: str
    email: EmailStr
    device_info: dict[str, Any]
    document_check_result: dict[str, Any]
    behaviour_summary: dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CaseListResponse(BaseModel):
    items: list[CaseRead]
    total: int
    limit: int
    offset: int


class AuditLogRead(BaseModel):
    id: UUID
    case_id: UUID | None = None
    event_type: str
    actor_type: str | None = None
    subject: str | None = None
    latency_ms: int | None = None
    meta: dict[str, Any] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}