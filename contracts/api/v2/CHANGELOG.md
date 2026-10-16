# Changelog

## v2.0.1 - Initial draft (unpublished)
- Draft of Adjustment Event API contract for group review. Not yet published.
- `POST /api/v2/adjustment` appends a manual correction to the append-only
  event store; there is no update or delete path.
- `AdjustmentEventCreate` request: `android_id`, optional `target_event_id` (an
  adjustment may point at another adjustment), a `corrected_fact` in the same
  vocabulary as the ingestion events, and the mandatory `reason` and `author`
  audit fields.
- `AdjustmentEventStored` response: all request fields plus the
  server-generated `adjustment_id`, `server_timestamp`, and `source` — the
  server-assigned origin of the write, never taken from the request body.


## v2.0.0
- Updated naming of "shifts" to "patrol sessions"
- Add timestamp to the patrol-session-event
- Renamed schemas to kebab-case: `ConnectionEvent` -> `connection-event`, `PatrolSessionEvent` -> `patrol-session-event`
- Replaced `GET /observations` and `GET /observation-events` with `GET /api/v2/dashboard`, `GET /api/v2/stations/{stationID}`, and `GET /api/v2/trains/{trainID}`.
- Replaced the flat `AreaObservation`/`ObservationEvent` beacon model with `Station`, `StationArea`, and `Train` entities, aggregated via `DashboardResponse`.
- Added `WS /stationUpdate` and `WS /trainUpdate` push channels, replacing the pollable `/observation-events` stream; each pushes the same payload as its corresponding `GET` endpoint (`StationResponse` / `TrainResponse`).


