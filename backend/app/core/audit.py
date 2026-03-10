from __future__ import annotations

from time import perf_counter
from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.models.audit_log import AuditLog


def now_ms() -> float:
    """High-resolution timer baseline for latency measurement."""
    return perf_counter()


def elapsed_ms(start: float) -> int:
    """Return elapsed milliseconds since start."""
    return int((perf_counter() - start) * 1000)


def write_audit_log(
    db: Session,
    event_type: str,
    actor_type: str,
    subject: str | None = None,
    case_id: str | None = None,
    latency_ms: int | None = None,
    metadata: dict | None = None,
):
    audit = AuditLog(
        id=uuid4(),
        case_id=case_id,
        event_type=event_type,
        actor_type=actor_type,
        subject=subject,
        latency_ms=latency_ms,
        meta=metadata or {},
    )

    db.add(audit)
    db.commit()