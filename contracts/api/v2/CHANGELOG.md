# Changelog

## v2.0.1 - Initial draft (unpublished)
- Positioning Interface: replaced `GET /api/v2/dashboard`,
  `GET /api/v2/stations/{stationID}`, `GET /api/v2/trains/{trainID}`,
  `WS /stationUpdate` and `WS /trainUpdate` with a single SSE stream,
  `GET /api/v2/dashboard/stream`, consumed by the control room and the Android
  app. The first event holds the full dashboard; later events hold only the
  changed stations and trains.
- Positioning Interface: `DashboardResponse` renamed to `Dashboard` and given a
  `time` field (when the event was sent). `StationResponse` and
  `TrainResponse` removed.
- Positioning Interface: `Station.slug` and `Station.station_name` replaced by
  `name`.
- Positioning Interface: added `GET /api/v2/config/at-risk-threshold` returning
  `AtRiskThreshold` with `at_risk_threshold_secs` — how much time must remain
  before an area becomes overdue for it to be considered at-risk.
- Positioning Interface: `StationArea` replaced by `Area` with `area_id`,
  `name`, `line`, `area_type`, `covered_now` and `overdue_at`. `beacon_id`,
  `slug`, `last_manned_at`, `current_steward_id` and `status` removed.
- `POST /api/v2/patrol-session/stop` now also closes open connections: the
  server appends a disconnect event (stamped with the stop `timestamp`) for
  every connect event of that `android_id` that has no matching disconnect,
  so clients no longer need to POST `/connection/disconnect` when a session
  ends.
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
- Draft of Coverage Stream API contract for group review. Not yet published.
- `GET /api/v2/coverage/stream` (ADR 0011): SSE events named `coverage`, each
  carrying a `CoverageSnapshot` — the coverage of **all** stations, never a
  single station. Agreed with the dashboard team: updates are handled like a
  reconnect, so a client always replaces its whole state, and the first event
  after (re)connecting is the snapshot. Recomputed when an ingestion event
  arrives and on a timer, because coverage also expires with time (ADR 0010).
- `StationCoverage`: `station_id`, station-level `status` rollup, and `areas`
  of `AreaCoverage` — `area_id`, `type`, `covered_now`, `stewards_present`,
  `last_covered_at`, `status`, absolute `overdue_at` (clients count down
  themselves), and `as_of` (the age of the verdict).
- Open question before publishing: the positioning-interface draft's
  `GET /api/v2/dashboard/stream` overlaps with this stream and still describes
  per-change updates; the two need to be reconciled.


## v2.0.0
- Updated naming of "shifts" to "patrol sessions"
- Add timestamp to the patrol-session-event
- Renamed schemas to kebab-case: `ConnectionEvent` -> `connection-event`, `PatrolSessionEvent` -> `patrol-session-event`
- Replaced `GET /observations` and `GET /observation-events` with `GET /api/v2/dashboard`, `GET /api/v2/stations/{stationID}`, and `GET /api/v2/trains/{trainID}`.
- Replaced the flat `AreaObservation`/`ObservationEvent` beacon model with `Station`, `StationArea`, and `Train` entities, aggregated via `DashboardResponse`.
- Added `WS /stationUpdate` and `WS /trainUpdate` push channels, replacing the pollable `/observation-events` stream; each pushes the same payload as its corresponding `GET` endpoint (`StationResponse` / `TrainResponse`).


