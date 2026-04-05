"""
Demo DAG: Bad SQL failure.
Runs a syntactically invalid SQL statement.
The agent should read the DAG source and identify the offending statement.
"""
import logging
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from utils import db_conn, on_failure_callback

log = logging.getLogger(__name__)


def run_invalid_sql(**context):
    conn = db_conn()
    try:
        with conn.cursor() as cur:
            # Syntax error: SELEKT is not valid SQL — intentional bad SQL
            cur.execute("SELEKT * FORM dag_run LIMIT 1;")
    finally:
        conn.close()


default_args = {
    "owner": "demo",
    "retries": 0,
    "on_failure_callback": on_failure_callback,
}

with DAG(
    dag_id="bad_sql_dag",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["demo", "bad_sql"],
) as dag:
    PythonOperator(
        task_id="run_invalid_query",
        python_callable=run_invalid_sql,
    )
