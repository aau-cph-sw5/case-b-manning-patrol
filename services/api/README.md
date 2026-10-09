# Manning Patrol Backend

Backend service for the Manning Patrol positioning system.

## Prerequisites

- Python 3.13
- [uv](https://github.com/astral-sh/uv) (Astral package manager)

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
├── src/
│   ├── main.py                  # FastAPI app definition and startup
│   ├── api/
│   │   └── v1/
│   │       └── routers/
│   │           ├── health.py
│   │           └── positioning_simulator.py # Positioning Interface simulator
│   ├── data/
│   │   └── stations.v1.json     # Station dataset, see data/README.md
│   ├── db/
│   │   ├── config.py            # Settings, reads DATABASE_URL
│   │   ├── main.py              # Engine, sessions, table creation
│   │   └── ingest.py            # Loads stations.v1.json into the database
│   ├── models/                  # Table models (station, patrol_area) and others
│   ├── scripts/                 # `uv run lint` / `uv run check` entry points
│   └── services/
│       ├── positioning_service.py
│       └── db/                  # Empty
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

- `WS /api/v1/ws/observation-events` - WebSocket stream of events

Fixture used:
- `fixtures/fixture-events-v1.json` - Event timeline replayed by the simulator

## Database

The backend uses PostgreSQL through SQLModel and the async `asyncpg` driver.

- `src/db/config.py` reads `DATABASE_URL` from the `.env`.
- `src/db/main.py` creates the engine and, on startup, creates the tables
  `station` and `patrolarea` if they do not exist.
- `src/db/ingest.py` then loads `src/data/stations.v1.json` into those tables.
  It replaces their contents on every start, so rows added by hand are lost.
  See `src/data/README.md`.

You need a PostgreSQL server and an empty database that `DATABASE_URL` points
to. `docker-compose.yml` is still a placeholder with no services, so
`docker compose up` does nothing yet; install PostgreSQL locally until it is
defined.

The tests do not need a running database. They set up an in-memory SQLite
database, and CI only sets a dummy `DATABASE_URL`.

## Tool Configuration

- **uv**: Package management
- **ruff**: Linter (E/F/I/N/W/UP rules, line-length 88)
- **ty**: Type checker (from Astral)
