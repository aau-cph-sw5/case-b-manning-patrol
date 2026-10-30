# Backend API

Python 3.13 / FastAPI backend service for the Manning/Patrol compliance system.

**Location:** `services/api/`

## Prerequisites

- Python 3.13
- [uv](https://github.com/astral-sh/uv) (Astral package manager)
- Docker (for local PostgreSQL)

## Running Locally

```bash
cd services/api
uv sync                          # install dependencies
docker compose up -d             # start PostgreSQL (port 5432)
cp .env-example .env             # set DATABASE_URL
uv run alembic upgrade head      # apply migrations
uv run dev                       # start with auto-reload on :8000
```

The `.env` file should contain:
```
DATABASE_URL=postgresql+asyncpg://metro:admin@localhost:5432/metro
```

## Development Commands

| Command | Description |
|---------|-------------|
| `uv run check` | Full CI check: sync, lint, typecheck, format, tests |
| `uv run lint` | Lint + type check only |
| `uv run ruff check src/` | Lint only |
| `uv run ty check src/` | Type check only |
| `uv run ruff format .` | Fix formatting |
| `uv run pytest` | Run tests |

## Project Structure

```
services/api/
├── alembic/                     # Database migrations
│   ├── env.py                   # Reads DATABASE_URL and SQLModel metadata
│   └── versions/                # Migration scripts
├── src/
│   ├── main.py                  # FastAPI app definition
│   ├── models/                  # Shared models (events, adjustments, beacons)
│   ├── api/
│   │   ├── v1/routers/          # v1 endpoints (simulator, adjustment)
│   │   └── v2/routers/          # v2 endpoints (dashboard SSE, health, ingestion)
│   ├── db/                      # Database layer (repositories, queries)
│   ├── services/                # Business logic (coverage, positioning, producer)
│   ├── scripts/                 # CLI entry points
│   └── data/                    # Reference data (stations)
├── fixtures/                    # Synthetic test data
├── tests/                       # pytest tests
├── docker-compose.yml           # Local PostgreSQL
├── pyproject.toml               # Dependencies and tool config
└── uv.lock                      # Locked dependency versions
```

## Database

The backend uses **PostgreSQL** through SQLModel and the async `asyncpg` driver.

- **Migrations:** Alembic manages the schema. Always apply migrations before starting the server:
  ```bash
  uv run alembic upgrade head
  ```

- **Creating a migration** after changing a model:
  ```bash
  uv run alembic revision --autogenerate -m "describe the change"
  uv run alembic upgrade head
  uv run alembic check         # verify models and migrations agree
  ```

- **Seeding:** Load the fixture event timeline:
  ```bash
  uv run python -m src.scripts.seed
  ```

- **Resetting:** Drop all tables and re-apply migrations:
  ```bash
  uv run reset-db
  ```

!!! warning "Migration gotcha"
    `create_all` runs on server startup. If you start the server before applying
    migrations, tables are created without Alembic's version record and
    `alembic upgrade head` will fail with "table already exists".

## Positioning Simulator

The API includes a simulator implementing the Positioning Interface contract
(`contracts/positioning-interface/v1/`):

- `GET /observations` — currently active area observations
- `GET /observation-events` — all observation events
- `GET /ws/observation-events` — WebSocket stream of events

Fixture: `fixtures/fixture-events-v1.json` — event timeline replayed by the simulator.

Run the simulator:
```bash
uv run positioning-simulator
```

## API Versions

| Version | Endpoints | Status |
|---------|-----------|--------|
| v1 | Simulator, adjustment (draft) | Legacy |
| v2 | Dashboard SSE, health, patrol session ingestion | Current |

See [Contracts Guide](contracts.md) for the versioning strategy.

## Production Deployment

```bash
uv sync --locked                 # install locked dependencies
export DATABASE_URL=...          # set as environment variable (not .env)
uv run alembic upgrade head      # apply migrations
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

Put a reverse proxy or process supervisor in front of the server.
