"""
Read-only Postgres query runner.
TODO: Implement real schema introspection queries.
"""
import logging

log = logging.getLogger(__name__)


async def query_schema_info(dag_id: str) -> str:
    # TODO: Query information_schema.columns for the table referenced in the DAG
    log.info("query_schema_info stub called for %s", dag_id)
    return f"[stub] Schema information for dag '{dag_id}' not yet queried from Postgres."
