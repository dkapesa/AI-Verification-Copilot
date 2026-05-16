from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


HumanOverrideDecision = Literal["APPROVE", "ESCALATE", "REJECT"]


class HumanOverrideCreate(BaseModel):
    decision: HumanOverrideDecision
    reason: str = Field(..., min_length=3, max_length=2000)


class HumanOverrideRead(BaseModel):
    id: UUID
    case_id: UUID
    decision: str
    reason: str
    actor_type: str
    original_ai_decision: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}