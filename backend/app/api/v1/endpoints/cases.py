from __future__ import annotations

from time import perf_counter
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.agents.schemas import AIReviewResponse, AggregatedSignal, DecisionOutput
from app.agents.service import run_ai_review
from app.api.v1.schemas.case import (
    AuditLogRead,
    CaseCreate,
    CaseListResponse,
    CaseRead,
)
from app.api.v1.schemas.human_override import (
    HumanOverrideCreate,
    HumanOverrideRead,
)
from app.api.v1.schemas.tools import (
    RunToolsRequest,
    RunToolsResponse,
    ToolResultResponse,
)
from app.core.audit import write_audit_log
from app.core.events import ActorType, AuditEvent
from app.crud.ai_review import get_latest_ai_review_for_case
from app.crud.case import (
    create_case,
    get_case,
    list_audit_logs_for_case,
    list_cases,
)
from app.crud.tool_runs import (
    create_tool_run,
    finalize_tool_run,
    get_latest_tool_runs_for_case,
)
from app.crud.human_override import (
    create_human_override,
    get_latest_human_override_for_case,
)
from app.db.deps import get_db
from app.services.tool_runner import run_tools_parallel
from app.tools.registry import tool_registry
from app.tools.schemas import ToolCaseInput

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("", response_model=CaseRead)
def create_case_endpoint(
    payload: CaseCreate,
    db: Session = Depends(get_db),
) -> CaseRead:
    t0 = perf_counter()

    case = create_case(db, payload)

    write_audit_log(
        db=db,
        event_type=AuditEvent.CASE_CREATED,
        actor_type=ActorType.SYSTEM,
        case_id=case.id,
        subject="case_created",
        latency_ms=int((perf_counter() - t0) * 1000),
        metadata={"case_id": str(case.id)},
    )

    return case


@router.get("/{case_id}", response_model=CaseRead)
def get_case_endpoint(
    case_id: UUID,
    db: Session = Depends(get_db),
) -> CaseRead:
    t0 = perf_counter()

    case = get_case(db, case_id)

    if not case:
        write_audit_log(
            db=db,
            event_type=AuditEvent.CASE_NOT_FOUND,
            actor_type=ActorType.SYSTEM,
            case_id=None,
            subject="case_not_found",
            latency_ms=int((perf_counter() - t0) * 1000),
            metadata={"case_id": str(case_id)},
        )
        raise HTTPException(status_code=404, detail="Case not found")

    write_audit_log(
        db=db,
        event_type=AuditEvent.CASE_VIEWED,
        actor_type=ActorType.SYSTEM,
        case_id=case.id,
        subject="case_viewed",
        latency_ms=int((perf_counter() - t0) * 1000),
        metadata={},
    )

    return case


@router.get("", response_model=CaseListResponse)
def list_cases_endpoint(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> CaseListResponse:
    t0 = perf_counter()

    items, total = list_cases(db, limit=limit, offset=offset)

    write_audit_log(
        db=db,
        event_type=AuditEvent.CASES_LISTED,
        actor_type=ActorType.SYSTEM,
        case_id=None,
        subject="cases_listed",
        latency_ms=int((perf_counter() - t0) * 1000),
        metadata={
            "limit": limit,
            "offset": offset,
            "returned": len(items),
            "total": total,
        },
    )

    return CaseListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{case_id}/audit-logs", response_model=list[AuditLogRead])
def get_case_audit_logs(
    case_id: UUID,
    db: Session = Depends(get_db),
) -> list[AuditLogRead]:
    case = get_case(db, case_id)

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    return list_audit_logs_for_case(db, case_id)


@router.post("/{case_id}/run-tools", response_model=RunToolsResponse)
async def run_tools_for_case(
    case_id: UUID,
    payload: RunToolsRequest,
    db: Session = Depends(get_db),
) -> RunToolsResponse:
    t0 = perf_counter()

    case = get_case(db, case_id)

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if payload.tool_names:
        unknown = [t for t in payload.tool_names if not tool_registry.has(t)]
        if unknown:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown tool names: {unknown}",
            )

    selected_tool_names = payload.tool_names or list(tool_registry.all().keys())

    case_input = ToolCaseInput(
        case_id=case.id,
        user_id=case.user_id,
        email=case.email,
        device_info=case.device_info or {},
        document_check_result=case.document_check_result or {},
        behaviour_summary=case.behaviour_summary or {},
    )

    write_audit_log(
        db=db,
        event_type=AuditEvent.TOOL_RUN_STARTED,
        actor_type=ActorType.SYSTEM,
        case_id=case.id,
        subject="tool_run",
        latency_ms=0,
        metadata={
            "tool_names": selected_tool_names,
            "requested_count": len(selected_tool_names),
        },
    )

    created_runs_by_tool: dict[str, object] = {}
    for tool_name in selected_tool_names:
        created_runs_by_tool[tool_name] = create_tool_run(
            db,
            case_id=case.id,
            tool_name=tool_name,
        )

    try:
        results = await run_tools_parallel(
            case_input,
            selected_tool_names,
        )

        for result in results:
            existing_run = created_runs_by_tool.get(result.tool_name)
            if existing_run is not None:
                finalize_tool_run(
                    db,
                    tool_run=existing_run,
                    result=result,
                )

        response_results = [
            ToolResultResponse(
                tool_name=result.tool_name,
                status=result.status,
                score=result.score,
                confidence=result.confidence,
                summary=result.summary,
            )
            for result in results
        ]

        statuses = {result.tool_name: result.status for result in results}
        failed_tools = [
            result.tool_name
            for result in results
            if str(result.status).upper() != "SUCCESS"
        ]

        write_audit_log(
            db=db,
            event_type=AuditEvent.TOOL_RUN_COMPLETED,
            actor_type=ActorType.SYSTEM,
            case_id=case.id,
            subject="tool_run",
            latency_ms=int((perf_counter() - t0) * 1000),
            metadata={
                "tool_names": [result.tool_name for result in results],
                "result_count": len(results),
                "statuses": statuses,
                "failed_tools": failed_tools,
            },
        )

        return RunToolsResponse(
            case_id=str(case.id),
            results=response_results,
        )

    except Exception as exc:
        write_audit_log(
            db=db,
            event_type=AuditEvent.TOOL_RUN_FAILED,
            actor_type=ActorType.SYSTEM,
            case_id=case.id,
            subject="tool_run",
            latency_ms=int((perf_counter() - t0) * 1000),
            metadata={
                "tool_names": selected_tool_names,
                "error": str(exc),
            },
        )
        raise


@router.get("/{case_id}/tool-runs", response_model=RunToolsResponse)
def get_case_tool_runs(
    case_id: UUID,
    db: Session = Depends(get_db),
) -> RunToolsResponse:
    case = get_case(db, case_id)

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    tool_runs = get_latest_tool_runs_for_case(db, case_id)

    response_results = [
        ToolResultResponse(
            tool_name=tool_run.tool_name,
            status=tool_run.status.value if hasattr(tool_run.status, "value") else str(tool_run.status),
            score=tool_run.score,
            confidence=tool_run.confidence,
            summary=tool_run.summary,
        )
        for tool_run in tool_runs
    ]

    return RunToolsResponse(
        case_id=str(case.id),
        results=response_results,
    )


@router.post("/{case_id}/ai-review", response_model=AIReviewResponse)
async def ai_review_case(
    case_id: UUID,
    db: Session = Depends(get_db),
) -> AIReviewResponse:
    case = get_case(db, case_id)

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    return await run_ai_review(
        db=db,
        case_id=case_id,
    )


@router.get("/{case_id}/ai-reviews/latest", response_model=AIReviewResponse)
def get_latest_ai_review(
    case_id: UUID,
    db: Session = Depends(get_db),
) -> AIReviewResponse:
    case = get_case(db, case_id)

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    review = get_latest_ai_review_for_case(db, case_id)

    if not review:
        raise HTTPException(status_code=404, detail="No AI review found for case")

    aggregated_signals_payload = review.aggregated_signals or {}
    tool_results_count = len(aggregated_signals_payload.get("tool_summaries", []))

    return AIReviewResponse(
        case_id=str(review.case_id),
        status="COMPLETED",
        decision=DecisionOutput(
            decision=review.decision,
            confidence=review.confidence,
            reasons=review.reasons or [],
            recommended_next_steps=review.recommended_next_steps or [],
        ),
        aggregated_signals=AggregatedSignal(**aggregated_signals_payload),
        tool_results_count=tool_results_count,
        errors=[],
    )


@router.post("/{case_id}/human-override", response_model=HumanOverrideRead)
def create_human_override_endpoint(
    case_id: UUID,
    payload: HumanOverrideCreate,
    db: Session = Depends(get_db),
) -> HumanOverrideRead:
    t0 = perf_counter()

    case = get_case(db, case_id)

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    latest_ai_review = get_latest_ai_review_for_case(db, case_id)
    original_ai_decision = latest_ai_review.decision if latest_ai_review else None

    override = create_human_override(
        db=db,
        case_id=case.id,
        payload=payload,
        original_ai_decision=original_ai_decision,
    )

    write_audit_log(
        db=db,
        event_type=AuditEvent.HUMAN_OVERRIDE_CREATED,
        actor_type=ActorType.HUMAN,
        case_id=case.id,
        subject="human_override",
        latency_ms=int((perf_counter() - t0) * 1000),
        metadata={
            "override_id": str(override.id),
            "decision": override.decision,
            "reason_length": len(override.reason),
            "original_ai_decision": override.original_ai_decision,
        },
    )

    return override


@router.get("/{case_id}/human-overrides/latest", response_model=HumanOverrideRead)
def get_latest_human_override(
    case_id: UUID,
    db: Session = Depends(get_db),
) -> HumanOverrideRead:
    case = get_case(db, case_id)

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    override = get_latest_human_override_for_case(db, case_id)

    if not override:
        raise HTTPException(status_code=404, detail="No human override found for case")

    return override