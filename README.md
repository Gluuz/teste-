# Projects & Tasks API

A small async FastAPI service for managing **Projects** and their **Tasks**, backed by PostgreSQL via SQLAlchemy 2.0 + asyncpg.

## Stack

- **FastAPI** — async REST API
- **SQLAlchemy 2.0 (async)** + **asyncpg** — DB access
- **PostgreSQL 16** — persistence (run via `docker compose`)
- **Pydantic v2** — request/response validation
- **pytest** + **pytest-asyncio** — unit, integration, and e2e tests
- **ruff** — linter and formatter

## Quickstart

```bash
# 1. configure env
cp .env.example .env

# 2. start postgres
docker compose up -d

# 3. install deps (Python 3.11)
python -m venv .venv
.venv/bin/pip install -r requirements.txt   # or: pip install fastapi uvicorn sqlalchemy asyncpg pydantic pytest pytest-asyncio

# 4. run the API
.venv/bin/uvicorn main:app --reload
```

The API will be available at <http://127.0.0.1:8000>. Interactive docs: `/docs`.

## Configuration

Environment variables (see `.env.example`):

| Var | Default | Purpose |
|-----|---------|---------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5332/postgres` | Async SQLAlchemy URL |
| `API_KEY` | `dev-secret` | Required in the `X-API-Key` header on every protected endpoint |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | `postgres` | Used by `docker-compose.yml` |
| `TEST_DATABASE_URL` | same as `DATABASE_URL` | Used by the integration test suite |

## Auth

Every endpoint except `/health` requires the header:

```
X-API-Key: dev-secret
```

In Swagger UI (`/docs`), click **Authorize** and paste the key once.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/projects/` | Create project |
| `GET`  | `/projects/{project_id}` | Get project |
| `PUT`  | `/projects/{project_id}` | Update project (partial) |
| `DELETE` | `/projects/{project_id}` | Delete project (cascades tasks) |
| `POST` | `/projects/{project_id}/tasks/` | Create task under project |
| `GET`  | `/projects/{project_id}/tasks/?limit=&offset=` | List tasks, sorted by `priority DESC` |
| `PUT`  | `/tasks/{task_id}` | Update task (partial) |
| `DELETE` | `/tasks/{task_id}` | Delete task |
| `GET`  | `/health` | Liveness check (no auth) |

### Example

```bash
H='X-API-Key: dev-secret'
curl -X POST http://127.0.0.1:8000/projects/ \
  -H "$H" -H 'Content-Type: application/json' \
  -d '{"name":"Apollo","description":"moon"}'

curl -X POST http://127.0.0.1:8000/projects/1/tasks/ \
  -H "$H" -H 'Content-Type: application/json' \
  -d '{"title":"build rocket","priority":10,"due_date":"2026-05-01"}'

curl 'http://127.0.0.1:8000/projects/1/tasks/?limit=10&offset=0' -H "$H"
```

## Data model

**Project** — `id`, `name`, `description?`, `created_at`
**Task** — `id`, `project_id` (FK, `ON DELETE CASCADE`), `title`, `priority` (int, higher = higher), `completed`, `due_date?`

A composite index `(project_id, priority)` keeps the priority-sorted list query cheap.

## Project layout

```
main.py                          FastAPI app + lifespan + 404 handler
src/
  exceptions.py                  NotFoundError (mapped to HTTP 404)
  infra/
    auth.py                      X-API-Key dependency
    database.py                  async engine, session factory, get_db
  models/                        SQLAlchemy ORM (Project, Task)
  routers/                       HTTP adapters (thin)
    schemas/                     Pydantic request/response models
  services/                      Business logic (DB orchestration)
tests/
  conftest.py                    engine + transactional db fixture
  unit/                          AsyncMock-based service tests
  integration/                   real-Postgres service tests
  e2e/                           HTTP-level tests via httpx + ASGITransport
```

Routers are intentionally thin — they parse input, call a service function, return the result. Services own all DB orchestration and raise `NotFoundError`, which an app-level handler maps to a 404 JSON response.

## Tests

```bash
# unit only (no Postgres needed)
.venv/bin/pytest tests/unit

# integration — services + real DB (requires `docker compose up -d`)
.venv/bin/pytest tests/integration

# e2e — full HTTP stack via httpx ASGITransport (requires Postgres too)
.venv/bin/pytest tests/e2e

# full suite
.venv/bin/pytest
```

Integration and e2e tests use SQLAlchemy's `join_transaction_mode="create_savepoint"` — every test runs inside an outer transaction that is rolled back on teardown, so commits inside services don't leak between tests. The e2e fixture overrides FastAPI's `get_db` dependency so HTTP requests hit the same transactional session.

## Lint & format

`ruff` is configured in `pyproject.toml` with rules `E/W/F/I/B/UP/SIM/C4/RUF`, line length 100, target `py311`.

```bash
.venv/bin/ruff check .          # lint
.venv/bin/ruff check --fix .    # lint + autofix
.venv/bin/ruff format .         # format
.venv/bin/ruff format --check . # CI: fail if anything would change
```
