from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.tool_run import ToolRun
from app.tools.schemas import ToolResult
from app.tools.types import ToolRunStatus


def create_tool_run(
    db: Session,
    *,
    case_id: UUID,
    tool_name: str,
) -> ToolRun:
    tool_run = ToolRun(
        case_id=case_id,
        tool_name=tool_name,
        status=ToolRunStatus.RUNNING,
        started_at=datetime.now(timezone.utc),
    )

    db.add(tool_run)
    db.commit()
    db.refresh(tool_run)

    return tool_run


def finalize_tool_run(
    db: Session,
    *,
    tool_run: ToolRun,
    result: ToolResult,
) -> ToolRun:
    tool_run.status = result.status
    tool_run.score = result.score
    tool_run.confidence = result.confidence
    tool_run.summary = result.summary
    tool_run.signals = result.signals
    tool_run.output = result.output
    tool_run.error_message = result.error_message
    tool_run.latency_ms = result.latency_ms
    tool_run.completed_at = result.completed_at

    db.add(tool_run)
    db.commit()
    db.refresh(tool_run)

    return tool_run


def get_latest_tool_runs_for_case(db: Session, case_id: UUID) -> list[ToolRun]:
    stmt = (
        select(ToolRun)
        .where(ToolRun.case_id == case_id)
        .order_by(
            ToolRun.tool_name.asc(),
            ToolRun.completed_at.desc(),
            ToolRun.started_at.desc(),
        )
    )

    rows = db.scalars(stmt).all()

    latest_by_tool: dict[str, ToolRun] = {}
    for row in rows:
        if row.tool_name not in latest_by_tool:
            latest_by_tool[row.tool_name] = row

    return list(latest_by_tool.values())