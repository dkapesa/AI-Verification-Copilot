from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.tools.types import ToolRunStatus


class ToolRun(Base):
    __tablename__ = "tool_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    tool_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    status: Mapped[ToolRunStatus] = mapped_column(
        Enum(ToolRunStatus, name="tool_run_status"),
        nullable=False,
        default=ToolRunStatus.PENDING,
        index=True,
    )

    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    signals: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    output: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )