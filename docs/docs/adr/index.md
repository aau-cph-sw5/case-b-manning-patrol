# Architecture Decision Records

ADRs document significant architectural decisions, their context, consequences,
and alternatives considered. They are **immutable** — when a decision changes,
a new ADR is created that supersedes the old one.

See [ADR-0001](0001-record-architectural-decision.md) for the ADR format and
numbering scheme.

## Index

| ADR | Title | Status | Date | Related Items |
|-----|-------|--------|------|---------------|
| [0001](0001-record-architectural-decision.md) | Record architectural decisions | Proposed | 2026-09-18 | — |
| [0002](0002-evidence-rule-decision.md) | Evidence rule decision | Accepted | 2026-09-18 | MET-B-001, 004, 005, 007, 014, 024 |
| [0003](0003-branching-strategy.md) | Branching strategy | Proposed | 2026-09-21 | — |
| [0004](0004-positioning-interface-contract.md) | Positioning interface contract | Accepted | 2026-09-23 | B-002 |
| [0005](0005-hosting-platform.md) | Hosting platform (Ucloud) | Proposed | 2026-09-23 | MET-B-004, 005, 012, 013, 020, 021, 023, 025 |
| [0006](0006-tolerated-gap-decision.md) | Tolerated gap decision | Proposed | 2026-10-05 | MET-B-004 |
| [0007](0007-database-decision.md) | PostgreSQL as database | Proposed | 2026-10-07 | MET-B-004, 013, 018–021, 023, 024 |
| [0008](0008-append-only-event-store-decision.md) | Append-only event store | Proposed | 2026-10-09 | MET-B-020 |
| [0009](0009-late-arriving-report-rule.md) | Late-arriving report rule | Accepted | 2026-10-16 | MET-B-006 |
| [0010](0010-patrol-completion.md) | Patrol completion | Proposed | 2026-10-16 | MET-B-007, 008, 009, 012–015, 024 |
| [0011](00011-server-sent-events.md) | Server-sent events for live updates | Proposed | 2026-10-19 | MET-B-007–009, 012–015, 024 |

## Status Legend

- **Proposed** — decision is suggested, not yet ratified
- **Accepted** — decision is ratified and in effect
- **Superseded** — replaced by a newer ADR (link in the ADR itself)

## Creating a New ADR

1. Copy the next sequential number (e.g., `0012-my-decision.md`)
2. Follow the structure defined in [ADR-0001](0001-record-architectural-decision.md):
   - Status, Date, Deciders, Related backlog items
   - Context — what is the issue?
   - Decision — what was decided?
   - Consequences — positive and negative impacts
   - Alternatives considered — what else was evaluated?
   - Notes — open questions, references
3. Only the **Status** field may be changed after creation
4. Add the new ADR to the navigation in `docs/mkdocs.yml`
