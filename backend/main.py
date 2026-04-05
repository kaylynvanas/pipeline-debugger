import logging
import os
import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agent.graph import run_agent
from db import Base, engine, get_db
from models import DiagnosisORM, DiagnosisResponse, TriggerPayload

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("Database tables ready")
    yield


app = FastAPI(title="Pipeline Debugger", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/trigger", response_model=DiagnosisResponse, status_code=202)
async def trigger(
    payload: TriggerPayload,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    diagnosis = DiagnosisORM(
        dag_id=payload.dag_id,
        task_id=payload.task_id,
        run_id=payload.run_id,
        status="investigating",
    )
    db.add(diagnosis)
    await db.commit()
    await db.refresh(diagnosis)

    background_tasks.add_task(run_agent, diagnosis.id, payload)

    log.info("Triggered agent for %s/%s (id=%s)", payload.dag_id, payload.task_id, diagnosis.id)
    return DiagnosisResponse.from_orm(diagnosis)


@app.get("/diagnoses", response_model=list[DiagnosisResponse])
async def list_diagnoses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DiagnosisORM).order_by(DiagnosisORM.created_at.desc())
    )
    return [DiagnosisResponse.from_orm(row) for row in result.scalars()]


@app.get("/diagnoses/{diagnosis_id}", response_model=DiagnosisResponse)
async def get_diagnosis(diagnosis_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DiagnosisORM).where(DiagnosisORM.id == diagnosis_id)
    )
    diagnosis = result.scalar_one_or_none()
    if not diagnosis:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    return DiagnosisResponse.from_orm(diagnosis)


@app.patch("/diagnoses/{diagnosis_id}/resolve", response_model=DiagnosisResponse)
async def resolve_diagnosis(diagnosis_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DiagnosisORM).where(DiagnosisORM.id == diagnosis_id)
    )
    diagnosis = result.scalar_one_or_none()
    if not diagnosis:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    if diagnosis.status == "resolved":
        raise HTTPException(status_code=409, detail="Diagnosis is already resolved")
    diagnosis.status = "resolved"
    await db.commit()
    await db.refresh(diagnosis)
    return DiagnosisResponse.from_orm(diagnosis)
