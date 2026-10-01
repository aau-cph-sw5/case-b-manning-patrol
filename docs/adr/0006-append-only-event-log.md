
# ADR 0006. Append Only Event Log

**Status.** Proposed
**Date.** 2026-09-23
**Deciders.** Sebastian Milo, Markus Eckstrøm, team 3
**Related backlog items.** MET-b-020

Blocks: MET-b-004, MET-b-013, MET-b-018, MET-b-019, MET-b-021, MET-b-023, MET-b-024

## Context

Metro Service delivers evidence of manning and patrol to Metroselskabet, and that evidence is only worth something if it cannot be quietly altered afterwards (see ADR 0002 on the contractual relation).
MET-b-020 requires that presence, patrol and manning records are stored append-only, that corrections are made as compensating events with the original still visible, that the event schema is versioned and documented, and that every write carries actor, server timestamp and source.

Tamper evidence cannot be added to a mutable store later without rebuilding everything built on top of it, which is why the storage decision is taken in sprint 2 rather than sprint 5.
ADR 0004 already established that the Android client sends connection events to the backend, and the positioning ingestion contract uses POST-only endpoints with an append-only log in mind.

The dashboard still needs fast answers to questions like "who is manning which station right now". Replaying the entire event history for every request is not realistic, so we also need a current-state view of the data.

## Decision

We will keep the event log in the same database as the rest of the system, as one `EventLog` table that is append-only.

> Three event types are written to the log: `ConnectionEvent`, `DisconnectionEvent` and `CorrectionEvent`.

> The frontends send events to the backend with a POST request. The endpoint appends the event to `EventLog` and updates the affected read models in the same database transaction, so the log and the read models cannot drift apart.

> The read models (e.g. current presence per station/train) are derived data. They may be updated and rebuilt, but the event log is the source of truth.

> No code path updates or deletes a row in `EventLog`. This is also enforced in the database, by giving the backend's database user insert and select rights only on the table so a bug or a direct query cannot change history either.

> A mistake is corrected by appending a `CorrectionEvent` that references the original event. The original event stays in the log and remains visible.

> The event schema is versioned and will be documented as a contract under `contracts/`, following the same structure as the existing positioning contracts.

## Consequences

### Positive impact:
-	Records cannot be changed without trace, which meets the requirement in MET-b-020.
-	One database means one technology to host, back up and learn on Ucloud (ADR 0005), and the event append and read model update can share one transaction.
-	The full history is available for audits and reports, and read models can be rebuilt from the log if they are ever wrong.
-	Having both the server timestamp and the device timestamp makes it visible when a device clock has been manipulated.

### Potential drawbacks:
-	Every write endpoint must remember to update the read models. Forgetting one gives a dashboard that disagrees with the log until it is rebuilt.
-	The log only grows. Storage and query performance on `EventLog` must be watched over time, and indexes will be needed.

## Alternatives considered

**Mutable tables with an audit log.** Normal CRUD tables with an audit table recording changes. Rejected, since the current data can still be edited and the audit log becomes a second, mutable source that must be trusted. MET-b-020 explicitly rules out a store where a record can be changed without trace.

**Separate event store (e.g. EventStoreDB or Kafka).** Purpose-built for append-only logs, but adds another service to host and learn on Ucloud and loses the shared transaction between the log and the read models. Too much for the scope of the project.

**Rebuilding state from the log on every read (no read models).** The simplest write path, but too slow for the live dashboard once the log grows.

## Notes

The concrete database engine is not chosen in this ADR.
The positioning ingestion contract also defines `ShiftEvent` (shift start/stop). It is an open question whether shift events should be written to the event log as well, since breaks affect manning evidence.
