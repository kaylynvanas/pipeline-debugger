"""
Demo DAG: Upstream failure.
Task A always fails. Task B depends on task A and is marked upstream_failed
by Airflow — it never executes. A reporter task (TriggerRule.ALL_DONE) always
runs last, detects any upstream_failed tasks, and posts them to the pipeline
debugger so the agent can diagnose the real root cause.
"""
import logging
import os
from datetime import datetime
from urllib.parse import quote

import requests
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule

from utils import on_failure_callback

log = logging.getLogger(__name__)

TRIGGER_URL = "http://fastapi:8000/trigger"
AIRFLOW_API = "http://airflow-webserver:8080/api/v1"
AIRFLOW_AUTH = (
    os.getenv("AIRFLOW_USERNAME", "airflow"),
    os.getenv("AIRFLOW_PASSWORD", "airflow"),
)


def task_a_always_fails(**context):
    raise RuntimeError("task_a: critical data load failed — source file not found")


def task_b_depends_on_a(**context):
    # This code is fine — task B never runs because task A failed upstream
    log.info("task_b: processing data from task_a output")


def report_upstream_failures(**context):
    """
    Runs after all tasks finish (TriggerRule.ALL_DONE).
    Finds any upstream_failed tasks and posts them to the pipeline debugger
    so the agent investigates from the downstream task's perspective.
    """
    dag_id = context["dag"].dag_id
    run_id = context["run_id"]

    try:
        response = requests.get(
            f"{AIRFLOW_API}/dags/{dag_id}/dagRuns/{quote(run_id, safe='')}/taskInstances",
            auth=AIRFLOW_AUTH,
            timeout=10,
        )
        response.raise_for_status()
        task_instances = response.json().get("task_instances", [])
    except Exception as exc:
        log.warning("Could not fetch task instances from Airflow API: %s", exc)
        return

    failed = [ti for ti in task_instances if ti["state"] == "failed"]
    upstream_failed = [ti for ti in task_instances if ti["state"] == "upstream_failed"]

    if not upstream_failed:
        return

    failed_sorted = sorted(failed, key=lambda ti: ti.get("start_date") or "")
    cause_task = failed_sorted[0]["task_id"] if failed_sorted else "an upstream task"
    for ti in upstream_failed:
        payload = {
            "dag_id": dag_id,
            "task_id": ti["task_id"],
            "run_id": run_id,
            "exception": f"Task skipped: upstream task '{cause_task}' failed",
            "log_url": "",
        }
        try:
            requests.post(TRIGGER_URL, json=payload, timeout=5)
            log.info("Reported upstream failure for task '%s'", ti["task_id"])
        except Exception as exc:
            log.warning("Failed to post to trigger endpoint: %s", exc)


default_args = {
    "owner": "demo",
    "retries": 0,
    "on_failure_callback": on_failure_callback,
}

with DAG(
    dag_id="upstream_failure_dag",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["demo", "upstream_failure"],
) as dag:
    task_a = PythonOperator(
        task_id="task_a_load_data",
        python_callable=task_a_always_fails,
    )

    task_b = PythonOperator(
        task_id="task_b_process_data",
        python_callable=task_b_depends_on_a,
    )

    reporter = PythonOperator(
        task_id="report_upstream_failures",
        python_callable=report_upstream_failures,
        trigger_rule=TriggerRule.ALL_DONE,
        # Reporter handles its own notification — no recursive callback needed
        on_failure_callback=None,
    )

    task_a >> task_b >> reporter
