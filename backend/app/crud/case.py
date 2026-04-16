from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.v1.schemas.case import CaseCreate
from app.db.models.audit_log import AuditLog
from app.db.models.case import Case


def create_case(db: Session, payload: CaseCreate) -> Case:
    case = Case(
        id=uuid4(),
        user_id=payload.user_id,
        email=payload.email,
        device_info=payload.device_info,
        document_check_result=payload.document_check_result,
        behaviour_summary=payload.behaviour_summary,
        status="PENDING",
    )

    db.add(case)
    db.commit()
    db.refresh(case)

    return case


def get_case(db: Session, case_id: UUID):
    stmt = select(Case).where(Case.id == case_id)
    return db.scalar(stmt)


def list_cases(db: Session, limit: int, offset: int):
    items = db.scalars(
        select(Case).offset(offset).limit(limit)
    ).all()

    total = db.scalar(select(func.count()).select_from(Case))

    return items, total


def list_audit_logs_for_case(db: Session, case_id: UUID):
    stmt = (
        select(AuditLog)
        .where(AuditLog.case_id == case_id)
        .order_by(AuditLog.created_at.desc())
    )
    return db.scalars(stmt).all()