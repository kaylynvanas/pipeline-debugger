"""
LangGraph agent graph.
Nodes: ingest → fetch_logs → classify → investigate → synthesise → persist
"""
import logging
import os
import uuid

from dotenv import load_dotenv

load_dotenv()

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from pydantic import BaseModel
from sqlalchemy import update

from agent.state import AgentState, ErrorCategory
from db import AsyncSessionLocal
from models import DiagnosisORM, TriggerPayload
from tools.airflow import fetch_task_logs, get_upstream_task_statuses
from tools.dag_reader import FilesystemDagReader
from tools.postgres import query_schema_info

log = logging.getLogger(__name__)

# Configure LangSmith tracing when API key is present — one place, opt-in
if os.getenv("LANGSMITH_API_KEY"):
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_API_KEY", os.environ["LANGSMITH_API_KEY"])
    os.environ.setdefault("LANGCHAIN_PROJECT", os.getenv("LANGSMITH_PROJECT", "pipeline-debugger"))
    log.info("LangSmith tracing enabled for project: %s", os.environ["LANGCHAIN_PROJECT"])

dag_reader = FilesystemDagReader()

# Lazy LLM initialisation — avoids import-time failure when ANTHROPIC_API_KEY is not yet set
_llm: ChatAnthropic | None = None


def get_llm() -> ChatAnthropic:
    global _llm
    if _llm is None:
        _llm = ChatAnthropic(model="claude-haiku-4-5-20251001", max_tokens=1024)
    return _llm


# --- Pydantic schemas for structured LLM output ---

class ClassifyOutput(BaseModel):
    error_category: ErrorCategory


class DiagnosisOutput(BaseModel):
    root_cause: str
    suggested_fix: str


# --- Nodes ---

def ingest(state: AgentState) -> dict:
    log.info(
        "Ingesting failure: dag=%s task=%s run=%s",
        state["dag_id"], state["task_id"], state["run_id"],
    )
    return {}


async def fetch_logs(state: AgentState) -> dict:
    logs = await fetch_task_logs(
        dag_id=state["dag_id"],
        run_id=state["run_id"],
        task_id=state["task_id"],
        log_url=state.get("log_url", ""),
    )
    log.info("Fetched logs for %s/%s (%d chars)", state["dag_id"], state["task_id"], len(logs))
    return {
        "raw_logs": logs,
        "evidence": [{"source": "airflow_logs", "content": logs}],
    }


async def classify(state: AgentState) -> dict:
    messages = [
        SystemMessage(content="You are an expert data engineer. Classify the root cause of an Airflow task failure."),
        HumanMessage(content=(
            f"DAG: {state['dag_id']}\n"
            f"Task: {state['task_id']}\n"
            f"Exception: {state.get('exception', '')}\n\n"
            f"Logs:\n{state['raw_logs']}\n\n"
            "Classify as exactly one of: schema_drift, bad_sql, upstream_failure, code_bug, unknown"
        )),
    ]
    structured_llm = get_llm().with_structured_output(ClassifyOutput)
    result: ClassifyOutput = await structured_llm.ainvoke(messages)
    log.info("Classified %s/%s as: %s", state["dag_id"], state["task_id"], result.error_category)
    return {"error_category": result.error_category}


async def investigate(state: AgentState) -> dict:
    category = state.get("error_category", "unknown")
    new_evidence: list[dict] = []

    if category == "schema_drift":
        result = await query_schema_info(state["dag_id"])
        new_evidence.append({"source": "postgres", "content": result})

    elif category in ("bad_sql", "code_bug"):
        source = dag_reader.read(state["dag_id"])
        new_evidence.append({"source": "dag_source", "content": source})

    elif category == "upstream_failure":
        result = await get_upstream_task_statuses(state["dag_id"], state["run_id"])
        new_evidence.append({"source": "airflow_logs", "content": result})

    log.info(
        "Investigation gathered %d evidence item(s) for %s (category=%s)",
        len(new_evidence), state["dag_id"], category,
    )
    return {"evidence": state.get("evidence", []) + new_evidence}


async def synthesise(state: AgentState) -> dict:
    evidence_text = "\n\n".join(
        f"[{e['source']}]\n{e['content']}" for e in state.get("evidence", [])
    )
    messages = [
        SystemMessage(content=(
            "You are an expert data engineer. Analyze the pipeline failure evidence "
            "and provide a clear, actionable diagnosis."
        )),
        HumanMessage(content=(
            f"DAG: {state['dag_id']}\n"
            f"Task: {state['task_id']}\n"
            f"Error category: {state.get('error_category', 'unknown')}\n"
            f"Exception: {state.get('exception', '')}\n\n"
            f"Evidence:\n{evidence_text}\n\n"
            "Provide:\n"
            "- root_cause: a plain-English explanation of what caused the failure\n"
            "- suggested_fix: specific, actionable steps to resolve it"
        )),
    ]
    structured_llm = get_llm().with_structured_output(DiagnosisOutput)
    result: DiagnosisOutput = await structured_llm.ainvoke(messages)
    log.info("Synthesised diagnosis for %s/%s", state["dag_id"], state["task_id"])
    return {"root_cause": result.root_cause, "suggested_fix": result.suggested_fix}


async def persist(state: AgentState) -> dict:
    diagnosis_id = uuid.UUID(state["diagnosis_id"])
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(DiagnosisORM)
            .where(DiagnosisORM.id == diagnosis_id)
            .values(
                status="diagnosed",
                error_category=state.get("error_category"),
                root_cause=state.get("root_cause"),
                evidence=state.get("evidence", []),
                suggested_fix=state.get("suggested_fix"),
            )
        )
        await session.commit()
    log.info("Persisted diagnosis %s", diagnosis_id)
    return {"status": "diagnosed"}


# --- Build graph ---

def _build_graph():
    g = StateGraph(AgentState)
    g.add_node("ingest", ingest)
    g.add_node("fetch_logs", fetch_logs)
    g.add_node("classify", classify)
    g.add_node("investigate", investigate)
    g.add_node("synthesise", synthesise)
    g.add_node("persist", persist)

    g.set_entry_point("ingest")
    g.add_edge("ingest", "fetch_logs")
    g.add_edge("fetch_logs", "classify")
    g.add_edge("classify", "investigate")
    g.add_edge("investigate", "synthesise")
    g.add_edge("synthesise", "persist")
    g.add_edge("persist", END)

    return g.compile()


_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = _build_graph()
    return _graph


async def run_agent(diagnosis_id: uuid.UUID, payload: TriggerPayload) -> None:
    log.info(
        "Agent started for diagnosis %s (dag=%s task=%s)",
        diagnosis_id, payload.dag_id, payload.task_id,
    )
    initial_state: AgentState = {
        "diagnosis_id": str(diagnosis_id),
        "dag_id": payload.dag_id,
        "task_id": payload.task_id,
        "run_id": payload.run_id,
        "exception": payload.exception,
        "log_url": payload.log_url,
        "raw_logs": "",
        "error_category": "unknown",
        "evidence": [],
        "root_cause": "",
        "suggested_fix": "",
        "status": "investigating",
    }
    try:
        await _get_graph().ainvoke(initial_state)
    except Exception:
        log.exception("Agent failed for diagnosis %s", diagnosis_id)
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(DiagnosisORM)
                .where(DiagnosisORM.id == diagnosis_id)
                .values(status="error")
            )
            await session.commit()
