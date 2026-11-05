# Contracts

Versioned OpenAPI interfaces that define how components communicate. Other teams
build against these contracts.

**Location:** `contracts/`

## Structure

```
contracts/
├── README.md
└── api/
    ├── v1/                          # Initial versions
    │   ├── CHANGELOG.md
    │   ├── positioning-interface/   # Observation events (simulator)
    │   │   ├── README.md
    │   │   └── schema.json
    │   └── positioning-ingestion/   # Connection events from Android
    │       ├── README.md
    │       └── schema.json
    └── v2/                          # Current versions
        ├── CHANGELOG.md
        ├── positioning-interface/   # Dashboard SSE stream
        ├── positioning-ingestion/   # Patrol session + connection events
        ├── positioning-adjustment/  # Manual adjustments (draft)
        └── health/                  # Health check endpoints
```

## Versioning Rules

Contracts are **published and immutable** — never edit a released version in place.
Add a new version directory instead.

### When to create a new major version

If the update **breaks the existing system** (URL changes, endpoints removed,
fields renamed):

1. Create a new directory (e.g., `v2/`) and copy the latest schema from the old version
2. Mark the old version as **deprecated** in its `README.md` and `schema.json`
   (`"deprecated": true` in OpenAPI)
3. Document the **sunset date** in the old version's `README.md` and `CHANGELOG.md`
4. Update the prefix throughout the repo so code and endpoint mounts point to
   the new contract

### When to bump minor version

If the change is **only an addition** (new optional fields or endpoints) and does
**not break the system**:

1. Update the `info.version` field in `schema.json` (e.g., `v1.0.0` → `v1.1.0`)
2. Document the change in the `CHANGELOG.md` of that version

### When to bump patch version

For **bug fixes** (typos, corrected examples):

1. Update the `info.version` field in `schema.json` (e.g., `v1.0.0` → `v1.0.1`)
2. Document the fix in the `CHANGELOG.md`

## CHANGELOG.md

Each versioned directory (`v1/`, `v2/`, etc.) must include a `CHANGELOG.md`
documenting changes for that version.

## Current Contracts

| Contract | Version | Description | Status |
|----------|---------|-------------|--------|
| Positioning Interface | v1 | Observation events (simulator) | Legacy |
| Positioning Interface | v2 | Dashboard SSE stream | Current |
| Positioning Ingestion | v1 | Connection events from Android | Legacy |
| Positioning Ingestion | v2 | Patrol session + connection events | Current |
| Positioning Adjustment | v2 | Manual adjustments | Draft |
| Health | v2 | Health check endpoints | Current |

## Related ADRs

- [ADR-0004: Positioning Interface Contract](../adr/0004-positioning-interface-contract.md) —
  Defines the observation-based design and source-of-truth decisions
