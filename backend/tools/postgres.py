"""
Read-only Postgres query runner.
Uses the shared SQLAlchemy engine from db.py (connection pooling included).
Never makes write queries.
"""
import logging

from sqlalchemy import text

from db import engine

log = logging.getLogger(__name__)


async def query_schema_info(_dag_id: str) -> str:
    """
    Query information_schema to return all columns in the public schema.
    The full schema dump is intentional — the LLM needs context about what
    columns *do* exist to reason about what's missing or misnamed.
    """
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT table_name, column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
            """))
            rows = result.fetchall()

        if not rows:
            return "No tables found in public schema."

        lines = []
        current_table = None
        for row in rows:
            if row.table_name != current_table:
                current_table = row.table_name
                lines.append(f"\nTable: {current_table}")
            nullable = "nullable" if row.is_nullable == "YES" else "not null"
            lines.append(f"  - {row.column_name}  {row.data_type}  ({nullable})")

        table_count = len({row.table_name for row in rows})
        log.info("Queried public schema: %d tables", table_count)
        return "\n".join(lines)
    except Exception as exc:
        log.warning("Schema query failed: %s", exc)
        return f"Could not query schema information: {exc}"
