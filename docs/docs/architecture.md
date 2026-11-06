# Architecture

## System Context

The Manning/Patrol Compliance System documents steward presence and patrol activity in the Copenhagen Metro during night operation. It consists of three deployable components that communicate through versioned contracts.

## Components

### Android App (Steward Client)
**Location:** `apps/android/`
**Stack:** Expo SDK 57, React Native, TypeScript

The steward-facing mobile app that:
- Scans BLE beacons to detect presence in station areas (concourse, platforms, trains)
- Manages patrol sessions (start/stop)
- Posts connection/disconnection events to the backend
- Receives real-time alerts via SSE

### Backend API
**Location:** `services/api/`
**Stack:** Python 3.13, FastAPI, SQLModel, PostgreSQL

The central service that:
- Ingests positioning and patrol events (append-only event store)
- Computes compliance metrics (manning %, patrol coverage)
- Serves the web dashboard via SSE
- Exposes versioned REST APIs defined in `contracts/`

### Web Dashboard
**Location:** `apps/web/`
**Stack:** Vite, React 19, TypeScript

The control-room dashboard that:
- Shows real-time compliance status (trains manned ≥ 70%, stations patrolled hourly)
- Displays historical records and overdue/at-risk stations
- Consumes live updates via Server-Sent Events (SSE)

## Data Flow

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│  Beacon BLE  │────────▶│ Android App  │────────▶│  Backend API │
│   (physical) │         │  (scanner)   │  POST   │  (ingestion) │
└──────────────┘         └──────────────┘         └──────┬───────┘
                                                         │
                              ┌──────────────────────────┼──────────────────────────┐
                              │                          ▼                          │
                              │                   ┌──────────────┐                  │
                              │                   │  PostgreSQL  │                  │
                              │                   │ Event Store  │                  │
                              │                   │  (append-only)│                 │
                              │                   └──────┬───────┘                  │
                              │                          │                          │
                              ▼                          ▼                          │
                       ┌──────────────┐          ┌──────────────┐                │
                       │ Web Dashboard│◀────────│   SSE Stream │◀───────────────┘
                       │  (React)     │  GET    │ (text/event- │
                       │              │         │   stream)    │
                       └──────────────┘         └──────────────┘
                              ▲
                              │ SSE (alerts)
                       ┌──────────────┐
                       │ Android App  │
                       │  (steward)   │
                       └──────────────┘
```

## Key Design Decisions

| Decision | ADR | Summary |
|----------|-----|---------|
| Positioning Interface | [ADR-0004](adr/0004-positioning-interface-contract.md) | Areas defined by beacons; Android is source of truth for timestamps |
| Database | [ADR-0007](adr/0007-database-decision.md) | PostgreSQL for relational + JSONB flexibility |
| Event Store | [ADR-0008](adr/0008-append-only-event-store-decision.md) | Append-only event store, no update/delete paths |
| Real-time Updates | [ADR-0011](adr/00011-server-sent-events.md) | Server-Sent Events for one-way server→client push |
| Train Manning Stream | [ADR-0012](adr/0012-train-manning-stream.md) | Trains on their own SSE stream for the web dashboard; stations stream shared with Android |
| Hosting | [ADR-0005](adr/0005-hosting-platform.md) | Ucloud (AAU) as staging environment |

## Compliance Rules

The system enforces two contractual requirements:

1. **Manning:** Trains must be manned ≥ 70% of running time
2. **Patrol:** Every station level (concourse, platform) must be patrolled at least once per rolling 60 minutes

Coverage is computed from the append-only event store, with late-arriving reports handled per [ADR-0009](adr/0009-late-arriving-report-rule.md).

### Manning percentages on the trains stream

The backend reports the manning ratio per stream event on `GET api/v2/trains/stream` as three fields: `manning_percent` (all trains), `m1m2_manning_percent` and `m3m4_manning_percent` (trains whose `line` contains M1/M2 or M3/M4). The ratio is manned time over running time, and the fields distinguish "no data" from "no manning":

- **null** when the group has no running time at all (e.g. no M3/M4 train has run yet) — there is nothing to compute a ratio against
- **0** when the group has running time but no manned time — the trains genuinely ran unmanned

See `contracts/api/v2/positioning-interface/README.md` for the full payload.

## Contracts

All inter-component communication goes through versioned OpenAPI contracts in `contracts/`:

```
contracts/api/
├── v1/                          # Initial versions
│   ├── positioning-interface/   # Observation events (simulator)
│   └── positioning-ingestion/   # Connection events from Android
└── v2/                          # Current versions
    ├── positioning-interface/   # Dashboard SSE stream
    ├── positioning-ingestion/   # Patrol session + connection events
    ├── positioning-adjustment/  # Manual adjustments (draft)
    └── health/                  # Health check endpoints
```

See [Contracts Guide](development/contracts.md) for versioning rules.
