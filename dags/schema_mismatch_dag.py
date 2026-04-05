"""
Demo DAG: Schema mismatch failure.
Tries to SELECT a column that doesn't exist in the dag_run table.
The agent should detect schema drift via an information_schema query.
"""
import logging
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from utils import db_conn, on_failure_callback

log = logging.getLogger(__name__)


def run_bad_query(**context):
    conn = db_conn()
    try:
        with conn.cursor() as cur:
            # This column does not exist — intentional schema mismatch
            cur.execute("SELECT nonexistent_column FROM dag_run LIMIT 1;")
    finally:
        conn.close()


default_args = {
    "owner": "demo",
    "retries": 0,
    "on_failure_callback": on_failure_callback,
}

with DAG(
    dag_id="schema_mismatch_dag",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["demo", "schema_drift"],
) as dag:
    PythonOperator(
        task_id="select_missing_column",
        python_callable=run_bad_query,
    )
