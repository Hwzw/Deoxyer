import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class JobStatus(enum.StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class OptimizationJob(Base):
    __tablename__ = "optimization_jobs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[str] = mapped_column(String(36), index=True)
    construct_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("constructs.id", ondelete="SET NULL")
    )
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.PENDING)
    input_sequence: Mapped[str] = mapped_column(Text)
    output_sequence: Mapped[str | None] = mapped_column(Text)
    parameters_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    cai_before: Mapped[float | None] = mapped_column(Float)
    cai_after: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
