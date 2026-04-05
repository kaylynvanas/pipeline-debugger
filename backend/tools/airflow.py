"""
Airflow REST API client.
TODO: Implement real Airflow API calls.
"""
import logging

log = logging.getLogger(__name__)


async def fetch_task_logs(dag_id: str, run_id: str, task_id: str, log_url: str = "") -> str:
    # TODO: GET /api/v1/dags/{dag_id}/dagRuns/{run_id}/taskInstances/{task_id}/logs/1
    log.info("fetch_task_logs stub called for %s/%s", dag_id, task_id)
    return f"[stub] Logs for task '{task_id}' in dag '{dag_id}' not yet fetched via Airflow API."


async def get_upstream_task_statuses(dag_id: str, run_id: str) -> str:
    # TODO: GET /api/v1/dags/{dag_id}/dagRuns/{run_id}/taskInstances
    log.info("get_upstream_task_statuses stub called for %s/%s", dag_id, run_id)
    return f"[stub] Upstream task statuses for dag '{dag_id}' run '{run_id}' not yet fetched."
