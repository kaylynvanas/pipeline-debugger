"""
Shared utilities for demo DAGs.
"""
import logging
import os
import requests
import psycopg2

log = logging.getLogger(__name__)

TRIGGER_URL = "http://fastapi:8000/trigger"


def db_conn():
    return psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ.get("POSTGRES_PORT", 5432)),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )


def on_failure_callback(context):
    payload = {
        "dag_id": context["dag"].dag_id,
        "task_id": context["task_instance"].task_id,
        "run_id": context["run_id"],
        "exception": str(context.get("exception", "")),
        "log_url": context["task_instance"].log_url,
    }
    try:
        requests.post(TRIGGER_URL, json=payload, timeout=5)
    except Exception as exc:
        log.warning("Failed to post to trigger endpoint: %s", exc)
