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

## Running

### Main Backend

```bash
# Development server with auto-reload (recommended)
uv run dev

# Or manually
uv run uvicorn manning_patrol_backend:app --reload --host 0.0.0.0 --port 8000
```

### Positioning Simulator

The simulator implements the Positioning Interface contract and replays fixture data.

```bash
# Run the simulator
uv run positioning-simulator
```

Both servers run on `http://localhost:8000` by default. Run only one at a time or use different ports.

## Development

### Lint + Type Check (one command)

```bash
uv run lint
```

This runs `ruff check src/ && ty check src/`

### Individual commands

```bash
# Lint only
uv run ruff check src/

# Type check only
uv run ty check src/
```

## Project Structure

```
manning-patrol-backend/
├── fixtures/
│   ├── fixture-shifts.json   # Shift data for simulator
│   └── mapping.json          # Beacon to station/train mapping
├── pyproject.toml    # Dependencies and tool config
├── uv.lock           # Locked dependency versions
├── .python-version   # Python version (3.13)
└── src/
    ├── manning_patrol_backend/
    │   └── __init__.py
    └── positioning_simulator.py  # Positioning Interface simulator
```

## Positioning Simulator

Implements the Positioning Interface contract (`contracts/positioning-interface/v1/`):

- `GET /observations` - Returns currently active area observations
- `GET /observation-events` - Returns all observation events
- `GET /ws/observation-events` - WebSocket stream of events

Fixtures used:
- `fixtures/fixture-shifts.json` - Raw shift/ping data
- `fixtures/mapping.json` - Beacon ID to station/train mapping

## Tool Configuration

- **uv**: Package management
- **ruff**: Linter (E/F/I/N/W/UP rules, line-length 88)
- **ty**: Type checker (from Astral)
