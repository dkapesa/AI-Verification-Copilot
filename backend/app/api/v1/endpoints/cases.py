from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.deps import get_db
from app.crud.case import create_case, get_case, list_cases
from app.api.v1.schemas.case import CaseCreate, CaseRead, CaseListResponse

from app.core.audit import write_audit_log, now_ms, elapsed_ms
from app.core.events import AuditEvent, ActorType

router = APIRouter()

@router.post("/cases", response_model=CaseRead)
def create_case_endpoint(payload: CaseCreate, db: Session = Depends(get_db)) -> CaseRead:
    t0 = now_ms()
    case = create_case(db, payload)
    write_audit_log(
        db=db,
        event_type=AuditEvent.CASE_CREATED,
        actor_type=ActorType.SYSTEM,
        case_id=case.id,
        subject="case_created",
        latency_ms=elapsed_ms(t0),
        metadata={"user_id": case.user_id},
    )
    return case


@router.get("/cases/{case_id}", response_model=CaseRead)
def get_case_endpoint(case_id: UUID, db: Session = Depends(get_db)) -> CaseRead:
    t0 = now_ms()
    case = get_case(db, case_id)

    if not case:
        # audit the failure too (optional but very realistic)
        write_audit_log(
            db=db,
            event_type=AuditEvent.CASE_NOT_FOUND,
            actor_type=ActorType.SYSTEM,
            case_id=None,
            subject="case_not_found",
            latency_ms=elapsed_ms(t0),
            metadata={"case_id": str(case_id)},
        )
        raise HTTPException(status_code=404, detail="Case not found")

    write_audit_log(
        db=db,
        event_type=AuditEvent.CASE_VIEWED,
        actor_type=ActorType.SYSTEM,
        case_id=case.id,
        subject="case_viewed",
        latency_ms=elapsed_ms(t0),
        metadata={},
    )
    return case

@router.get("/cases", response_model=CaseListResponse)
def list_cases_endpoint(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> CaseListResponse:
    t0 = now_ms()
    items, total = list_cases(db, limit=limit, offset=offset)

    write_audit_log(
        db=db,
        event_type=AuditEvent.CASES_LISTED,
        actor_type=ActorType.SYSTEM,
        case_id=None,
        subject="cases_listed",
        latency_ms=elapsed_ms(t0),
        metadata={"limit": limit, "offset": offset, "returned": len(items), "total": total},
    )

    return CaseListResponse(items=items, total=total, limit=limit, offset=offset)