"""
Airflow REST API client.
All calls are read-only — never modifies Airflow state.
"""
import logging
import os
from urllib.parse import quote

import httpx

log = logging.getLogger(__name__)

# Resolved lazily so load_dotenv() in the app entry point fires first
_config: tuple[str, tuple[str, str]] | None = None


def _get_config() -> tuple[str, tuple[str, str]]:
    global _config
    if _config is None:
        _config = (
            os.getenv("AIRFLOW_BASE_URL", "http://localhost:8080"),
            (os.getenv("AIRFLOW_USERNAME", "airflow"), os.getenv("AIRFLOW_PASSWORD", "airflow")),
        )
    return _config


async def fetch_task_logs(dag_id: str, run_id: str, task_id: str, log_url: str = "") -> str:
    """Fetch raw task logs from the Airflow REST API."""
    base_url, auth = _get_config()
    encoded_run_id = quote(run_id, safe="")
    url = (
        f"{base_url}/api/v1/dags/{dag_id}"
        f"/dagRuns/{encoded_run_id}"
        f"/taskInstances/{task_id}/logs/1"
    )
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                url,
                auth=auth,
                headers={"Accept": "text/plain"},
            )
            response.raise_for_status()
            log.info("Fetched logs for %s/%s (%d chars)", dag_id, task_id, len(response.text))
            return response.text
    except httpx.HTTPStatusError as exc:
        log.warning("Airflow logs request failed: %s %s", exc.response.status_code, url)
        return f"Could not fetch logs: HTTP {exc.response.status_code}"
    except httpx.RequestError as exc:
        log.warning("Airflow logs request error: %s", exc)
        return f"Could not reach Airflow API: {exc}"


async def get_upstream_task_statuses(dag_id: str, run_id: str) -> str:
    """Fetch all task instance statuses for a DAG run."""
    base_url, auth = _get_config()
    encoded_run_id = quote(run_id, safe="")
    url = f"{base_url}/api/v1/dags/{dag_id}/dagRuns/{encoded_run_id}/taskInstances"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, auth=auth)
            response.raise_for_status()
            data = response.json()

        lines = []
        for ti in data.get("task_instances", []):
            lines.append(
                f"task_id={ti['task_id']}  state={ti['state']}  "
                f"start={ti.get('start_date', 'n/a')}  end={ti.get('end_date', 'n/a')}"
            )
        result = "\n".join(lines) if lines else "No task instances found."
        log.info("Fetched %d task statuses for %s/%s", len(lines), dag_id, run_id)
        return result
    except httpx.HTTPStatusError as exc:
        log.warning("Airflow task instances request failed: %s %s", exc.response.status_code, url)
        return f"Could not fetch task statuses: HTTP {exc.response.status_code}"
    except httpx.RequestError as exc:
        log.warning("Airflow task instances request error: %s", exc)
        return f"Could not reach Airflow API: {exc}"
