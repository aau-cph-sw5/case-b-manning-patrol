# Coverage Stream API

DRAFT - NOT PUBLISHED.

Backend API contract for pushing live station patrol coverage (MET-B-007) to the control room dashboard and the steward app over Server-Sent Events, as decided in [ADR 0011](../../../docs/adr/00011-server-sent-events.md).

## Endpoint

- `GET api/v2/coverage/stream` - Server-Sent Events stream ([CoverageSnapshot])

## Stream behavior

Every message is an SSE event named `coverage` whose `data` is a JSON array of
[StationCoverage], one entry per station.

- The first event after connecting contains the coverage as of the last refresh.
- Each following event contains the **full coverage of all stations** for one
  refresh - never a single station. This was agreed with the dashboard team:
  updates are handled like a reconnect, so a client always replaces its whole
  state instead of merging, and a missed event is impossible without a broken
  connection, which reconnects and receives a fresh full event.
- Refreshes happen when a positioning or patrol session event arrives and on a
  timer, because coverage also expires with time: a patrol slides out of the
  rolling sixty-minute window without any event arriving ([ADR 0010](../../../docs/adr/0010-patrol-completion.md)).

## Data models

### CoverageSnapshot
Array of [StationCoverage]. One event's `data`.

### StationCoverage
- `station_id`: String - the client keys its state by this id
- `status`: `compliant` | `overdue` - rollup: overdue if any area is overdue
- `areas`: [AreaCoverage] - concourse and platform, evaluated independently

### AreaCoverage
- `area_id`: String
- `type`: `platform` | `concourse`
- `covered_now`: Boolean - a qualifying visit is still open
- `stewards_present`: String[] - stewards currently at the area
- `last_covered_at`: ISO 8601 date-time | null - null when never patrolled
- `status`: `compliant` | `overdue` - against the rolling sixty-minute window
- `overdue_at`: ISO 8601 date-time | null - absolute deadline; clients count
  down themselves
- `as_of`: ISO 8601 date-time - when this verdict was computed

## Implementation notes

The fan-out is in memory, so the stream works in a single process only. A
client that disconnects is unsubscribed immediately; EventSource
auto-reconnects and receives a fresh first event with the full coverage.

The positioning-interface contract's `GET /api/v2/dashboard/stream` carries
station reference data and trains alongside its own view of areas; the two
streams overlap and should be reconciled before either is published.
