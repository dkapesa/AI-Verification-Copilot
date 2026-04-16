from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter

from sqlalchemy.orm import Session

from app.core.audit import write_audit_log
from app.core.events import TOOL_RUN_STARTED, TOOL_RUN_COMPLETED, TOOL_RUN_FAILED
from app.crud.tool_runs import create_tool_run, finalize_tool_run
from app.db.models.case import Case
from app.tools.device_risk import device_risk_check, TOOL_NAME
from app.tools.schemas import ToolCaseInput, ToolResult
from app.tools.types import ToolRunStatus


async def run_device_risk_tool(
    db: Session,
    *,
    case: Case,
):
    """
    Execute device_risk_check and persist results.
    """

    write_audit_log(
        db,
        event_type=TOOL_RUN_STARTED,
        actor_type="system",
        subject=f"case:{case.id}",
        case_id=case.id,
        metadata={"tool_name": TOOL_NAME},
    )

    tool_run = create_tool_run(
        db,
        case_id=case.id,
        tool_name=TOOL_NAME,
    )

    start = perf_counter()
    started_at = datetime.now(timezone.utc)

    try:

        tool_input = ToolCaseInput(
            case_id=case.id,
            user_id=case.user_id,
            email=case.email,
            device_info=case.device_info or {},
            document_check_result=case.document_check_result or {},
            behaviour_summary=case.behaviour_summary or {},
        )

        result = await device_risk_check(tool_input)

        latency_ms = int((perf_counter() - start) * 1000)

        result = result.model_copy(
            update={
                "latency_ms": latency_ms,
                "started_at": started_at,
                "completed_at": datetime.now(timezone.utc),
            }
        )

        tool_run = finalize_tool_run(
            db,
            tool_run=tool_run,
            result=result,
        )

        write_audit_log(
            db,
            event_type=TOOL_RUN_COMPLETED,
            actor_type="system",
            subject=f"case:{case.id}",
            case_id=case.id,
            metadata={
                "tool_name": TOOL_NAME,
                "tool_run_id": str(tool_run.id),
                "score": result.score,
                "confidence": result.confidence,
            },
        )

        return tool_run

    except Exception as exc:

        latency_ms = int((perf_counter() - start) * 1000)

        failed_result = ToolResult(
            tool_name=TOOL_NAME,
            status=ToolRunStatus.FAILED,
            error_message=str(exc),
            latency_ms=latency_ms,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )

        tool_run = finalize_tool_run(
            db,
            tool_run=tool_run,
            result=failed_result,
        )

        write_audit_log(
            db,
            event_type=TOOL_RUN_FAILED,
            actor_type="system",
            subject=f"case:{case.id}",
            case_id=case.id,
            metadata={
                "tool_name": TOOL_NAME,
                "error": str(exc),
            },
        )

        return tool_run