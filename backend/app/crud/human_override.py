from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.schemas.human_override import HumanOverrideCreate
from app.db.models.human_override import HumanOverride


def create_human_override(
    *,
    db: Session,
    case_id: UUID,
    payload: HumanOverrideCreate,
    original_ai_decision: str | None = None,
) -> HumanOverride:
    record = HumanOverride(
        case_id=case_id,
        decision=payload.decision,
        reason=payload.reason.strip(),
        actor_type="human",
        original_ai_decision=original_ai_decision,
        created_at=datetime.now(UTC),
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


def get_latest_human_override_for_case(
    db: Session,
    case_id: UUID,
) -> HumanOverride | None:
    stmt = (
        select(HumanOverride)
        .where(HumanOverride.case_id == case_id)
        .order_by(HumanOverride.created_at.desc())
    )

    return db.scalar(stmt)