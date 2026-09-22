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
# Development server with auto-reload
uv run uvicorn manning_patrol_backend:app --reload

# Or use the entry point
uv run manning-patrol-backend
```

### Positioning Simulator

The simulator implements the Positioning Interface contract and replays fixture data.

```bash
# Run the simulator
uv run positioning-simulator
```

Both servers run on `http://localhost:8000` (simulator will need a different port if running alongside main backend).

## Development

### Linting

```bash
uv run ruff check src/
```

### Type checking

```bash
uv run mypy src/
```

### Run both

```bash
uv run ruff check src/ && uv run mypy src/
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
- **mypy**: Type checker (Python 3.13, strict mode)
