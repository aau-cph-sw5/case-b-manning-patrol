# Manning Patrol Backend

Backend service for the Manning Patrol positioning system.

## Prerequisites

- `>=Python 3.13`
- `>=uv 0.13.0` (Astral package manager)

## Running as a developer (step by step)

- Run `uv sync` — installs dependencies.
- Run `docker compose up -d` — starts the PostgreSQL container (host port 5433 must be free; 5432 is often taken by a local PostgreSQL install).
- Create `services/api/.env` with `DATABASE_URL=postgresql+asyncpg://metro:admin@localhost:5433/metro` (see `.env-example`).
- Run `uv run alembic upgrade head` — applies migrations (before the first server start).
- Run `uv run dev` — starts the server with auto-reload on `http://localhost:8000`.

## Running in production (step by step)

- Run `uv sync --locked` — installs the locked dependencies (same as CI).
- Run `export DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/DATABASE_NAME` — set it as a real environment variable, not a `.env` file. Remember to fill in ` USER ` `PASSWORD ` `HOST`and `DATABASE_NAME`
- Run `uv run alembic upgrade head` — applies migrations against the production database.
- Run `uv run uvicorn src.main:app --port 8000` — starts the server.

## Development

- Run `uv run check` — full CI check, run before pushing: `uv sync --locked`, `ruff check`, `ty check`, `ruff format --check`, `pytest`.
- Run `uv run lint` — lint + type check only: `ruff check src/ && ty check src/`.
- Run `uv run ruff check src/` — lint only.
- Run `uv run ty check src/` — type check only.
- Run `uv run ruff format .` — fix formatting before `check` complains.
- Run `uv run verify-chain` — checks every hash chain in the database from `DATABASE_URL` and prints, per chain, `OK`, `empty` (no links, nothing verified) or the first broken link and its reason, plus how many events or adjustments have no chain link. Exit codes: 0 if every chain is intact, 1 if a chain is broken or has unlinked entries, 2 if the database could not be read. The app always saves an entry with its link, so unlinked entries mean direct database writes. On a dev database migrated from before the hash chain format changed, run `uv run reset-db` first, or old links are reported as broken.

CI also runs `alembic upgrade head` and `alembic check` against a PostgreSQL
service container, so a model change without a matching migration fails the
build (see [Migrations](#migrations)).

## Project Structure

```
services/api/
├── alembic/             # Database migrations
├── src/
│   ├── main.py          # App startup and long-lived objects
│   ├── api/             # Routers, schemas and dependencies (v2)
│   ├── authorization/   # Role-based access control
│   ├── data/            # Reference data loaded at startup
│   ├── db/              # Tables, queries and engine setup
│   ├── domain/          # Value objects and enums, no storage or API imports
│   ├── scripts/         # Entry points for `uv run` commands
│   ├── security/        # Current user from the request
│   └── services/        # Business logic (coverage, manning, records, hash chain, ...)
├── tests/               # Unit and integration tests
├── .env-example         # Template for your local .env (DATABASE_URL)
├── .python-version      # Python version (3.13)
├── alembic.ini          # Alembic config; database URL comes from the environment
├── CONTRIBUTING.md      # Backend coding rules
├── docker-compose.yml   # Local PostgreSQL database for development
├── pyproject.toml       # Dependencies, tool config and `uv run` commands
└── uv.lock              # Locked dependency versions
```

## Database

The backend uses PostgreSQL through SQLModel and the async `asyncpg` driver.
See [Running as a developer](#running-as-a-developer-step-by-step) for the
full setup: `docker-compose.yml` defines the local PostgreSQL container
(fixed credentials `metro` / `admin`, published on host port 5433), and `.env-example` shows the`DATABASE_URL` format.

- `src/db/config.py` reads `DATABASE_URL` from the environment or the `.env`
  file. Alembic reads the same setting, so `alembic.ini` holds no database
  URL. Without `DATABASE_URL` the app falls back to a local SQLite file
  (`local.db`).


### Migrations

- Run `uv run alembic upgrade head` — apply migrations.
- After changing a table in `src/db/models/`, generate a migration, read it, and commit it with the model change:

  ```bash
  uv run alembic revision --autogenerate -m "describe the change"
  uv run alembic upgrade head
  uv run alembic check    # passes when the models and migrations agree
  ```

  Note: autogenerate compares against your current database, so run
  `upgrade head` first. Review the generated file: it does not detect renames
  (it emits a drop and an add, losing data), and adding a `nullable=False`
  column to a table with rows needs a default or a backfill.

### Resetting the database

- Run `uv run reset-db` — drops every table (including `alembic_version`) and re-applies all migrations. Stations, lines and patrol areas are re-ingested on the next server start; other rows (events, adjustments) are lost. Use `docker compose down -v` to start completely fresh.

## Reconstructing a past shift

`uv run reconstruct` rebuilds station coverage and train manning for one
shift from the stored events, using the same calculation as the live
dashboard. It only reads the database from `DATABASE_URL`.

```bash
uv run reconstruct --date 2026-11-03
uv run reconstruct --date 2026-11-03 --known-at 2026-11-03T05:30+01:00
uv run reconstruct --date 2026-11-03 --json
```

- `--date` is the local date the shift starts on. The night shift runs
  00:00-06:00 Copenhagen time, so `2026-11-03` is the night of 2-3 November.
  Events are placed in the shift by when the phone saw them
  (`device_timestamp`).
- `--known-at` reproduces the picture as it was known at that moment: only
  events the backend had received by then (`server_timestamp`) are used, and
  the shift is evaluated no later than that time. It must include a timezone.
  Without it, every stored event counts, including ones that arrived late.
- `--json` prints machine-readable output with times in UTC; the default
  table shows local times.
- A shift that has not started yet exits with status 1.

The reconstruction uses today's stations, patrol areas, trains and patrol
rules, and does not apply adjustments.
