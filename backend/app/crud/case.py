from sqlalchemy.orm import Session
from sqlalchemy import select, func
from uuid import uuid4

from app.db.models.case import Case
from app.api.v1.schemas.case import CaseCreate


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


def get_case(db: Session, case_id):
    stmt = select(Case).where(Case.id == case_id)
    return db.scalar(stmt)


def list_cases(db: Session, limit: int, offset: int):
    items = db.scalars(
        select(Case).offset(offset).limit(limit)
    ).all()

    total = db.scalar(select(func.count()).select_from(Case))

    return items, total