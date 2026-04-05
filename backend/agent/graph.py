"""
LangGraph agent — stub.
Receives a trigger payload, runs the investigation graph, and persists the diagnosis.
Full implementation in Week 2 tasks 2–4.
"""
import logging
import uuid

from sqlalchemy import update

from db import AsyncSessionLocal
from models import DiagnosisORM, TriggerPayload

log = logging.getLogger(__name__)


async def run_agent(diagnosis_id: uuid.UUID, payload: TriggerPayload) -> None:
    log.info("Agent started for diagnosis %s (dag=%s task=%s)", diagnosis_id, payload.dag_id, payload.task_id)
    # TODO: replace with full LangGraph graph
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(DiagnosisORM)
                .where(DiagnosisORM.id == diagnosis_id)
                .values(status="diagnosed", root_cause="[stub] Full agent not yet implemented.")
            )
            await session.commit()
        log.info("Agent stub finished for diagnosis %s", diagnosis_id)
    except Exception:
        log.exception("Agent failed for diagnosis %s", diagnosis_id)
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(DiagnosisORM)
                .where(DiagnosisORM.id == diagnosis_id)
                .values(status="error")
            )
            await session.commit()
