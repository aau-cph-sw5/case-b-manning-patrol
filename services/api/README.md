# Manning Patrol Backend

Backend service for the Manning Patrol positioning system.

## Prerequisites

- Python 3.13
- [uv](https://github.com/astral-sh/uv) (Astral package manager)
- Docker for Windows/MacOS (running the VM where the database container lives)
    - If Linux or WSL2, container can run native in the OS. Search for setup yourself.

## Setup

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

The app reads its database address from `DATABASE_URL`, and it will not start
without it. Create `services/api/.env` and insert your personal `DATABASE_URL`:

```
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/DATABASE_NAME
```

## Running

```bash
# Development server with auto-reload (recommended)
uv run dev

# Or manually
uv run fastapi dev src/main.py
```

The server runs on `http://localhost:8000`. The positioning simulator is
included in the main app (see below), so there is no separate server to start.

## Development

### Lint + Type Check (one command)

```bash
uv run lint
```

This runs `ruff check src/ && ty check src/`

### Full CI check (run before pushing)

```bash
uv run check
```

This runs the same steps as CI: `uv sync --locked`, `ruff check`, `ty check`, `ruff format --check`, and `pytest`.

CI additionally runs `alembic upgrade head` and `alembic check` against a
PostgreSQL service container, so a model change without a matching migration
fails the build. Run them locally against your database before pushing a
model change (see [Migrations](#migrations)).

### Individual commands

```bash
# Lint only
uv run ruff check src/

# Type check only
uv run ty check src/
```

## Project Structure

```
services/api/
├── alembic/
│   ├── env.py                   # Reads DATABASE_URL and SQLModel metadata
│   └── versions/                # Migration scripts, applied in order
├── alembic.ini
├── src/
│   ├── main.py                  # FastAPI app definition and startup
│   ├── models/                  # Shared models (events, adjustments, beacons)
│   │   ├── coverage.py          # Coverage and overdue log value objects (MET-B-007, skeleton)
│   │   └── dashboard.py         # Dashboard stream payload (contracts/positioning-interface v2)
│   ├── db/repository/           # Database query functions; overdue_log.py is the overdue log (skeleton)
│   ├── api/
│   │   ├── v1/
│   │   │   └── routers/
│   │   │       ├── adjustment.py       # Adjustment route (contracts/positioning-adjustment v1, draft)
│   │   │       ├── health.py           # Health check endpoint
│   │   │       └── positioning_simulator.py # Positioning Interface simulator
│   │   └── v2/
│   │       └── routers/
│   │           ├── patrol_session.py   # Connection and patrol-session ingestion routes (contracts/positioning-ingestion v2)
│   │           └── dashboard_stream.py # SSE dashboard stream (contracts/positioning-interface v2)
│   ├── scripts/                 # `uv run lint` / `uv run check` entry points
│   └── services/
│       ├── coverage/            # Patrol coverage computation, overdue tracking and SSE publishing (MET-B-007, skeleton)
│       ├── positioning_service.py
│       ├── db/                  # Empty
│       └── producer.py          # Event/adjustment producer
├── fixtures/
│   └── fixture-events-v1.json   # Event timeline replayed by the simulator
├── tests/
├── docker-compose.yml # Local PostgreSQL database (not yet defined)
├── pyproject.toml    # Dependencies and tool config
├── uv.lock           # Locked dependency versions
└── .python-version   # Python version (3.13)
```

## Positioning Simulator

Implements the Positioning Interface contract (`contracts/positioning-interface/v1/`):

- `GET /observations` - Returns currently active area observations
- `GET /observation-events` - Returns all observation events
- `GET /ws/observation-events` - WebSocket stream of events

Fixture used:
- `fixtures/fixture-events-v1.json` - Event timeline replayed by the simulator

## Database

The backend uses PostgreSQL through SQLModel and the async `asyncpg` driver.
> **Status:** Docker-Compose PostgreSQL setup

Run Docker for Windows/MacOS, make sure the engine(Virtual Machine) is running.
See '.env-example' for .env setup.

- `src/db/config.py` reads `DATABASE_URL` from the `.env`. Alembic reads the
  same setting, so `alembic.ini` holds no database URL.
- The schema is managed by Alembic migrations in `alembic/versions/`.
- `src/db/main.py` creates the engine and still runs `create_all` on server
  startup. Apply migrations before starting the server on a new database,
  otherwise the tables are created without Alembic's version record and
  `alembic upgrade head` will fail with "table already exists".
- `src/db/ingest.py` then loads `src/data/stations.v1.json` into those tables.
  It replaces their contents on every start, so rows added by hand are lost.
  See `src/data/README.md`.

- `docker-compose.yml` — defines the PostgreSQL setup.
- `src/services/db/` — hold the database access layer (connection
  setup, queries).
  
Make sure port 5432 is available before utilizing the docker setup- 
if you have used a local postgres dB prior then it most likely is 
occupying that port( previous db setup)
 
Once the database service is defined, start it from '.../services/api/':

```bash
docker compose up -d
uv run alembic upgrade head
```

### Migrations

After pulling changes, bring your database up to date:

```bash
uv run alembic upgrade head
```

After changing a model in `src/models/`, generate a migration, read it, and
commit it with the model change:

```bash
uv run alembic revision --autogenerate -m "describe the change"
uv run alembic upgrade head
uv run alembic check    # passes when the models and migrations agree
```

Autogenerate compares the models against your current database, so run
`upgrade head` first, otherwise the migration also contains changes that are
already in earlier migrations. Review the generated file: autogenerate does not
detect renames (it emits a drop and an add, losing data) and adding a
`nullable=False` column to a table with rows needs a default or a backfill.

### Seeding

```bash
uv run python -m src.scripts.seed
```

Applies pending migrations, then inserts the fixture event timeline. Running it
again only inserts rows that are missing.

### Resetting the database

If your database is in a state migrations cannot fix (for example, tables
created by an older server start before Alembic), reset it with:

```bash
uv run reset-db
```

This drops every table, including Alembic's `alembic_version`, and re-applies
all migrations. Stations, lines and patrol areas are re-ingested from
`src/data/stations.v1.json` on the next server start, but any other rows
(events, adjustments) are lost. Tables that no longer exist in the models are
not dropped; use `docker compose down -v` to start completely fresh.

## Tool Configuration

- **uv**: Package management
- **ruff**: Linter (E/F/I/N/W/UP rules, line-length 88)
- **ty**: Type checker (from Astral)
