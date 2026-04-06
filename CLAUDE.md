# CLAUDE.md

This file provides context for AI coding assistants working in this repository.

## What this project is

An agentic pipeline debugger. When an Apache Airflow DAG task fails, a LangGraph agent automatically investigates the root cause by fetching task logs, querying Postgres, and reading DAG source code. It produces a structured diagnosis (error category, evidence, root cause, suggested fix) that is persisted to Postgres and displayed in a React dashboard. All agent runs are traced in LangSmith.

## Tech stack

- **Agent:** LangGraph + LangSmith
- **Backend:** FastAPI + asyncpg + Pydantic
- **Orchestrator:** Apache Airflow (runs via Docker Compose)
- **Database:** Postgres
- **Frontend:** React + TypeScript + Vite + TanStack Query + Tailwind CSS

## Project structure

```
pipeline-debugger/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── agent/
│   │   ├── graph.py         # LangGraph graph definition
│   │   └── state.py         # TypedDict state schema
│   ├── tools/
│   │   ├── airflow.py       # Airflow REST API client
│   │   ├── postgres.py      # Read-only Postgres query runner
│   │   └── dag_reader.py    # DAG source file reader
│   ├── models.py            # Pydantic schemas + SQLAlchemy models
│   └── db.py                # Postgres connection
├── frontend/
│   └── src/
│       ├── App.tsx
│       ├── components/
│       │   ├── DiagnosisPanel.tsx
│       │   ├── ErrorBoundary.tsx
│       │   ├── FailuresList.tsx
│       │   └── FailuresSkeleton.tsx
│       └── api.ts
├── dags/
│   ├── schema_mismatch_dag.py
│   ├── bad_sql_dag.py
│   ├── upstream_failure_dag.py
│   └── utils.py                 # shared on_failure_callback + db_conn
├── docker-compose.yml
├── .env.example
└── CLAUDE.md
```

## Local development setup

### Requirements
- Docker Desktop
- Python 3.11
- Node.js 24+

### Environment variables
Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```

Required keys:
```
ANTHROPIC_API_KEY=
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=pipeline-debugger
AIRFLOW_BASE_URL=http://localhost:8080
AIRFLOW_USERNAME=airflow
AIRFLOW_PASSWORD=airflow
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=airflow
POSTGRES_USER=airflow
POSTGRES_PASSWORD=airflow
```

### Start the stack
```bash
docker compose up -d
```

This starts Airflow (webserver + scheduler + worker), Postgres, and the FastAPI backend. The FastAPI container mounts `./backend` and runs with `--reload`, so code changes are picked up automatically.

### Frontend (React)
```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`, backend at `http://localhost:8000`, Airflow UI at `http://localhost:8080`.

## API endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/trigger` | Receives Airflow on_failure_callback, starts agent |
| GET | `/diagnoses` | List all diagnoses, newest first |
| GET | `/diagnoses/{id}` | Single diagnosis by id |
| PATCH | `/diagnoses/{id}/resolve` | Mark as resolved |

## LangGraph agent

The graph processes failures through these nodes in order:

1. `ingest` — parse DAG id, task id, run id from the webhook payload
2. `fetch_logs` — call Airflow REST API to retrieve raw task logs
3. `classify` — LLM classifies the error: `schema_drift` | `bad_sql` | `upstream_failure` | `code_bug` | `unknown`
4. `investigate` — tool calls branch by category (Postgres query, DAG source read, upstream task check)
5. `synthesise` — LLM produces a structured Diagnosis object
6. `persist` — save diagnosis to Postgres, update status

## Diagnosis schema

```python
class Evidence(BaseModel):
    source: str      # "airflow_logs" | "postgres" | "dag_source"
    content: str

class Diagnosis(BaseModel):
    dag_id: str
    task_id: str
    run_id: str
    error_category: str
    root_cause: str
    evidence: list[Evidence]
    suggested_fix: str
    status: str      # "investigating" | "diagnosed" | "error"
    created_at: datetime
```

## Code conventions

- Python: type hints everywhere, Pydantic for all data models, async/await throughout
- No synchronous database calls in FastAPI routes — use `asyncpg` or async SQLAlchemy
- All LLM calls go through LangGraph nodes — never call the LLM directly outside the graph
- Environment variables loaded via `python-dotenv` — never hardcode keys
- React components in TypeScript — no `.jsx` files
- TanStack Query for all data fetching — no raw `fetch` calls in components

## Things to avoid

- Do not commit `.env` — it is in `.gitignore`
- Do not use `WidthType.PERCENTAGE` in any table definitions
- Do not make write queries to Postgres from agent tools — read-only only
- Do not use `print()` for logging — use Python's `logging` module
- Do not call Airflow's internal database directly — use the Airflow REST API only

## Demo DAGs

Three DAGs in `/dags/` are used for demos and testing:

- `schema_mismatch_dag.py` — fails because it SELECTs a column that doesn't exist
- `bad_sql_dag.py` — fails because of a syntax error in a SQL statement
- `upstream_failure_dag.py` — task B fails because task A always fails first

Each DAG has `on_failure_callback` pointing to `POST http://localhost:8000/trigger`.
