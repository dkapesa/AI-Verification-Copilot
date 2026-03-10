import enum
import uuid

from sqlalchemy import String, DateTime, Enum, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CaseStatus(str, enum.Enum):
    PENDING = "PENDING"
    REVIEWED = "REVIEWED"
    ESCALATED = "ESCALATED"


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)

    device_info: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict
    )

    document_check_result: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict
    )

    behaviour_summary: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict
    )

    status: Mapped[CaseStatus] = mapped_column(
        Enum(CaseStatus, name="case_status"),
        nullable=False,
        default=CaseStatus.PENDING,
        index=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )