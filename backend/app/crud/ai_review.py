# backend/app/crud/ai_review.py
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.ai_review import AIReview


def create_ai_review(
    *,
    db: Session,
    case_id: UUID,
    decision: str,
    confidence: float,
    reasons: list[str],
    recommended_next_steps: list[str],
    aggregated_signals: dict[str, Any],
    reasoning_summary: str | None,
    model_provider: str | None,
    model_name: str | None,
    prompt_version: str | None,
    retry_count: int,
    latency_ms: int | None,
) -> AIReview:
    record = AIReview(
        case_id=case_id,
        decision=decision,
        confidence=confidence,
        reasons=reasons,
        recommended_next_steps=recommended_next_steps,
        aggregated_signals=aggregated_signals,
        reasoning_summary=reasoning_summary,
        model_provider=model_provider,
        model_name=model_name,
        prompt_version=prompt_version,
        retry_count=retry_count,
        latency_ms=latency_ms,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_latest_ai_review_for_case(db: Session, case_id: UUID) -> AIReview | None:
    stmt = (
        select(AIReview)
        .where(AIReview.case_id == case_id)
        .order_by(AIReview.created_at.desc())
    )
    return db.scalar(stmt)