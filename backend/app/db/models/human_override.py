from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class HumanOverride(Base):
    __tablename__ = "human_overrides"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    case_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    decision = Column(String(32), nullable=False, index=True)

    reason = Column(Text, nullable=False)

    actor_type = Column(String(64), nullable=False, default="human")

    original_ai_decision = Column(String(32), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())