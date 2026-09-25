# Changelog

## v2.0.0 - Station/train model, dashboard endpoints, WS updates

- **Breaking:** Replaced `GET /observations` and `GET /observation-events` with `GET /api/v1/dashboard`, `GET /api/v1/stations/{stationID}`, and `GET /api/v1/trains/{trainID}`.
- **Breaking:** Replaced the flat `AreaObservation`/`ObservationEvent` beacon model with `Station`, `StationArea`, and `Train` entities, aggregated via `DashboardResponse`.
- Added `WS /stationUpdate` and `WS /trainUpdate` push channels, replacing the pollable `/observation-events` stream; each pushes the same payload as its corresponding `GET` endpoint (`StationResponse` / `TrainResponse`).

## v1.0.0 - Initial version

- Initial release of Positioning Interface API contract
- Added AreaObservation and ObservationEvent schemas
- Added GET /observations and GET /observation-events endpoints
