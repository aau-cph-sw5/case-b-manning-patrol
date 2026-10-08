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
│   ├── main.py                  # FastAPI app definition
│   ├── models.py
│   ├── api/
│   │   └── v1/
│   │       └── routers/
│   │           └── positioning_simulator.py # Positioning Interface simulator
│   ├── scripts/                 # `uv run lint` / `uv run check` entry points
│   └── services/
│       ├── positioning_service.py
│       └── db/                  # Database access layer (planned, empty)
├── fixtures/
│   └── fixture-events-v1.json   # Event timeline replayed by the simulator
├── tests/
├── docker-compose.yml # Local PostgreSQL database (planned, not yet defined)
├── pyproject.toml    # Dependencies and tool config
├── uv.lock           # Locked dependency versions
└── .python-version   # Python version (3.13)
```

## Positioning Simulator

Implements the Positioning Interface contract (`contracts/positioning-interface/v1/`):

- `WS /api/v1/ws/observation-events` - WebSocket stream of events

Fixtures used:
- `fixtures/fixture-shifts.json` - Raw shift/ping data
- `fixtures/mapping.json` - Beacon ID to station/train mapping

## Database

> **Status:** Docker-Compose PostgreSQL setup

Run Docker for Windows/MacOS, make sure the engine(Virtual Machine) is running.
See '.env-example' for .env setup.

The backend will use PostgreSQL, run locally via Docker Compose:

- `docker-compose.yml` — defines the PostgreSQL setup.
- `src/services/db/` — will hold the database access layer (connection
  setup, queries). Currently empty.

Once the database service is defined, start it from '.../services/api/':

```bash
docker compose up -d
```

## Tool Configuration

- **uv**: Package management
- **ruff**: Linter (E/F/I/N/W/UP rules, line-length 88)
- **ty**: Type checker (from Astral)
