# backend/app/db/models/ai_review.py
from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.base import Base


class AIReview(Base):
    __tablename__ = "ai_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    decision = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)

    reasons = Column(JSONB, nullable=False, default=list)
    recommended_next_steps = Column(JSONB, nullable=False, default=list)
    aggregated_signals = Column(JSONB, nullable=False, default=dict)

    reasoning_summary = Column(Text, nullable=True)

    model_provider = Column(String, nullable=True)
    model_name = Column(String, nullable=True)
    prompt_version = Column(String, nullable=True)

    retry_count = Column(Integer, nullable=False, default=0)
    latency_ms = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())