from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlalchemy import DateTime, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class DiagnosisORM(Base):
    __tablename__ = "diagnoses"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    dag_id: Mapped[str] = mapped_column(Text, nullable=False)
    task_id: Mapped[str] = mapped_column(Text, nullable=False)
    run_id: Mapped[str] = mapped_column(Text, nullable=False)
    error_category: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    suggested_fix: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="investigating")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# --- Pydantic schemas ---

class Evidence(BaseModel):
    source: str   # "airflow_logs" | "postgres" | "dag_source"
    content: str


class TriggerPayload(BaseModel):
    dag_id: str
    task_id: str
    run_id: str
    exception: str = ""
    log_url: str = ""


class DiagnosisResponse(BaseModel):
    id: UUID
    dag_id: str
    task_id: str
    run_id: str
    error_category: Optional[str]
    root_cause: Optional[str]
    evidence: list[Evidence]
    suggested_fix: Optional[str]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm(cls, obj: DiagnosisORM) -> "DiagnosisResponse":
        data = {**obj.__dict__}
        data["evidence"] = [Evidence(**e) for e in (obj.evidence or [])]
        return cls.model_validate(data)
