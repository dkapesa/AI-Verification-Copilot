from pydantic import BaseModel, EmailStr
from typing import Any
from uuid import UUID
from datetime import datetime


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