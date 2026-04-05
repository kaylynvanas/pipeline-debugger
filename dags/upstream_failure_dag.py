"""
Demo DAG: Upstream failure.
Task A always fails. Task B depends on task A and is marked upstream_failed
by Airflow — it never executes. The on_failure_callback fires for task A.
The agent should identify that task A is the true root cause.
"""
import logging
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from utils import on_failure_callback

log = logging.getLogger(__name__)


def task_a_always_fails(**context):
    raise RuntimeError("task_a: critical data load failed — source file not found")


def task_b_depends_on_a(**context):
    # This code is fine — task B never runs because task A failed upstream
    log.info("task_b: processing data from task_a output")


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

    task_a >> task_b
