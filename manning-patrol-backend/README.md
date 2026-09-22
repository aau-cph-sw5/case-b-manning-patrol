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

```bash
# Development server with auto-reload
uv run uvicorn manning_patrol_backend:app --reload

# Or use the entry point
uv run manning-patrol-backend
```

Server runs on `http://localhost:8000`

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
├── pyproject.toml    # Dependencies and tool config
├── uv.lock           # Locked dependency versions
├── .python-version   # Python version (3.13)
└── src/
    └── manning_patrol_backend/
        └── __init__.py
```

## Tool Configuration

- **uv**: Package management
- **ruff**: Linter (E/F/I/N/W/UP rules, line-length 88)
- **mypy**: Type checker (Python 3.13, strict mode)
