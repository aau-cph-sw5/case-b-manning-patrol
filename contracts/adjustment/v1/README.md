# Adjustment Event API

**Status: DRAFT — not published.** This contract is under review and not yet
versioned as a published interface. Breaking changes may still be made without
a new version folder.

Backend API contract for the Web dashboard to append manual correction events
to the append-only event store. Adjustments correct the real state shown on
dashboards and in reports without modifying or deleting any recorded history.

## Architecture

```mermaid
graph TD
    WebUI[Web UI Admin Dashboard\\nReact] -->|POST /api/v1/adjustments| RestAPI
    RestAPI[RestAPI] --> Store[Append-only event store]
    Store --> Replay[Projection layer]
    Replay -->|Corrected manning/patrol state| Dashboards
```

## Endpoints

- `POST /api/v1/adjustments` - Append an [AdjustmentEvent] to the event store

## Implementation Notes

**Adjustments are events, not mutations.** An adjustment is appended to the
same append-only store as connection and shift events (see the Positioning
Ingestion contract). There is no update or delete path anywhere in the system:
history is never rewritten, and the "real state" is defined as the projection
that accounts for adjustments.

**Adjustment types.**

- `void` — marks one previously recorded event as erroneous. The event stays
  in the store, but downstream projections (manning percentages, patrol times)
  must skip it. Requires `target_event_id`.
- `compensate` — records a fact that the original events got wrong or never
  recorded (e.g. a beacon that never fired, or a wrong device timestamp).
  Requires `corrected_fact`. May also carry `target_event_id` to link the
  correction to the event it supersedes, but this is optional.

**Chained adjustments.** `target_event_id` may reference another adjustment:
if an adjustment is itself wrong, it is corrected by appending a new
adjustment, never by editing the previous one.

**Audit criteria.** Every write to the store carries `actor`, `author`,
`source`, and a server-generated `server_timestamp`. `reason` is mandatory:
this store is contractual evidence of compliance (see ADR 0002), so the
justification travels with the correction.

**Authorization.** `author` identifies the admin performing the correction
and is taken from the authenticated dashboard session, not from the request
body.

**Projection behavior.** Consumers replaying the log handle adjustments as
follows:

1. `void` with `target_event_id` — skip the target event when computing state.
2. `compensate` with `corrected_fact` — treat as a normal connect, disconnect,
   shift start, or shift stop occurring at `corrected_fact.occurred_at`.

## Data Models

### AdjustmentEvent (request)

- `actor`: UUID — the steward (android device) the adjustment is about
- `adjustment_type`: enum `"void"` | `"compensate"`
- `target_event_id`: UUID — the event being corrected; required for `void`,
  optional for `compensate`, null when the adjustment has no single target
- `corrected_fact`: [CorrectedFact] — required for `compensate`, null for `void`
- `reason`: string — mandatory human-readable justification
- `author`: UUID — the admin who performed the adjustment (from session)
- `source`: enum `"dashboard"` | `"api"` | `"simulator"` | `"import"`

### AdjustmentEvent (response)

All request fields, plus:

- `adjustment_id`: UUID — server-generated identifier of the appended event
- `server_timestamp`: date-time — when the backend recorded the adjustment, UTC
  in ISO 8601 with offset

### CorrectedFact

- `fact_type`: enum `"connect"` | `"disconnect"` | `"shift_start"` |
  `"shift_stop"` — the event that actually happened
- `beacon_id`: UUID — required when `fact_type` is `connect` or `disconnect`,
  null otherwise
- `occurred_at`: date-time — when the corrected fact actually happened
