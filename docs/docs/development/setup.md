# Development Setup

Each component installs and runs independently — there is no root-level install.

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Node.js | 20 or 22 | Web dashboard, Android app |
| npm | >= 11.4.2 | Package management |
| Python | >= 3.13 | Backend API |
| [uv](https://docs.astral.sh/uv/) | latest | Python package manager |
| Docker | latest | Local PostgreSQL for backend |

## Quick Start

### 1. Backend API

```bash
cd services/api
uv sync                          # install dependencies
docker compose up -d             # start PostgreSQL on port 5432
cp .env-example .env             # configure DATABASE_URL
uv run alembic upgrade head      # apply migrations
uv run dev                       # start server on http://localhost:8000
```

Full check (lint, types, format, tests):
```bash
uv run check
```

See [Backend Guide](backend.md) for details.

### 2. Web Dashboard

```bash
cd apps/web
npm install
npm run dev                      # Vite dev server
```

Build and type-check:
```bash
npm run build                    # tsc -b && vite build
npm run lint                     # oxlint
npm test                         # vitest
```

See [Web Dashboard Guide](web.md) for details.

### 3. Android App

```bash
cd apps/android
npm install
EXPO_PUBLIC_API_URL=http://<your-lan-ip>:8000 npx expo start
```

Type-check and lint:
```bash
npx tsc --noEmit
npm run lint
```

See [Android App Guide](android.md) for details.

### 4. Documentation (this site)

```bash
cd docs
uv sync
uv run mkdocs serve              # live-reloading docs server
```

Build for deployment:
```bash
uv run mkdocs build               # outputs to docs/site/
uv run mkdocs gh-deploy           # deploy to GitHub Pages
```

## Branching Strategy

- `main` — protected, demonstrated work only
- `development` — shared integration branch
- `feature/<item-id>-<description>` — one branch per backlog item

See [ADR-0003: Branching Strategy](../adr/0003-branching-strategy.md).

## Contributing

The contribution process is shared across all semester products and lives in the
[semester documentation hub](https://github.com/aau-cph-sw5/semester-docs).

Key documents:
- [Onboarding](https://github.com/aau-cph-sw5/semester-docs/blob/main/docs/01-onboarding.md)
- [Ways of working](https://github.com/aau-cph-sw5/semester-docs/blob/main/docs/02-ways-of-working.md)
- [Pull request process](https://github.com/aau-cph-sw5/semester-docs/blob/main/docs/03-pull-request-process.md)
- [Handling Metro material](https://github.com/aau-cph-sw5/semester-docs/blob/main/docs/10-data-handling.md)
