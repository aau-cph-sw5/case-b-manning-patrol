# Manning/Patrol Compliance System

A compliance-grade system documenting that stewards are present and active during night operation, against a contractual requirement that:

- **Trains are manned at least 70%** of their running time
- **Every station level is patrolled** at least once per rolling 60 minutes

With a verifiable real-time and historical record.

!!! info "Semester Project"
    5th Semester, BSc Software Engineering, AAU Copenhagen · Autumn 2026

## System Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Android App    │────▶│   Backend API   │◀────│  Web Dashboard  │
│  (Steward App)  │     │  (FastAPI/Python)│     │  (React/Vite)   │
│                 │     │                 │     │                 │
│ • Beacon scan   │     │ • Event store   │     │ • Real-time SSE │
│ • Patrol session│     │ • Coverage calc │     │ • Historical    │
│ • Position post │     │ • Contract APIs │     │   views         │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │
         │              ┌────────┴────────┐
         └─────────────▶│    PostgreSQL   │
                        │  (Event store)  │
                        └─────────────────┘
```

## Repository Layout

| Directory | Description |
|-----------|-------------|
| `apps/android/` | Steward-facing Android app (Expo / React Native) |
| `apps/web/` | Control-room dashboard (Vite + React 19 + TypeScript) |
| `services/api/` | Backend service (Python 3.13 / FastAPI) |
| `contracts/` | Versioned API interfaces (OpenAPI) other teams build against |
| `docs/` | Architecture Decision Records (ADRs) and this documentation site |

## Quick Links

- [Architecture](architecture.md) — System design and data flow
- [Development Setup](development/setup.md) — Get the system running locally
- [Backend API](development/backend.md) — FastAPI service guide
- [Web Dashboard](development/web.md) — React dashboard guide
- [Android App](development/android.md) — Steward app guide
- [Contracts](development/contracts.md) — API contract versioning
- [ADRs](adr/index.md) — Architecture Decision Records

## Data Handling

!!! warning "Synthetic Data Only"
    This product runs on **synthetic steward identities** for the whole semester.
    No personal data is transferred to AAU. Never commit anything Metro supplied —
    this repository is public.
