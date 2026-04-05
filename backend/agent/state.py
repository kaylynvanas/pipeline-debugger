from typing import Literal, TypedDict

ErrorCategory = Literal["schema_drift", "bad_sql", "upstream_failure", "code_bug", "unknown"]
DiagnosisStatus = Literal["investigating", "diagnosed", "error"]


class AgentState(TypedDict):
    diagnosis_id: str           # UUID as string — LangGraph state must be serialisable
    dag_id: str
    task_id: str
    run_id: str
    exception: str
    log_url: str
    raw_logs: str
    error_category: ErrorCategory
    evidence: list[dict]        # list of {"source": str, "content": str}
    root_cause: str
    suggested_fix: str
    status: DiagnosisStatus
