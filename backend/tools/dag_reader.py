"""
DAG source file reader.

Defines a DagSourceReader protocol so the agent is not coupled to the filesystem.
FilesystemDagReader is the default implementation for local/Docker use.
"""
import logging
import os
from typing import Protocol, runtime_checkable

log = logging.getLogger(__name__)


@runtime_checkable
class DagSourceReader(Protocol):
    def read(self, dag_id: str) -> str:
        ...


class FilesystemDagReader:
    def __init__(self, dags_path: str | None = None):
        self.dags_path = os.path.realpath(dags_path or os.getenv("DAGS_PATH", "/dags"))

    def read(self, dag_id: str) -> str:
        # Resolve the full path and verify it stays inside dags_path (prevent traversal)
        path = os.path.realpath(os.path.join(self.dags_path, f"{dag_id}.py"))
        if not path.startswith(self.dags_path + os.sep):
            log.warning("Blocked path traversal attempt for dag_id=%s", dag_id)
            return "Invalid DAG id."
        try:
            with open(path) as f:
                content = f.read()
            log.info("Read DAG source for %s (%d chars)", dag_id, len(content))
            return content
        except FileNotFoundError:
            log.warning("DAG source not found at %s", path)
            return f"DAG source not found: {path}"
