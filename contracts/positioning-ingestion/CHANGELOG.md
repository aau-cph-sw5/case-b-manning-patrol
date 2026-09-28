# Changelog

## v2.0.0 - Split connection/shift endpoints, add timestamp

- **Breaking:** Split `POST /connection-event` into `POST /connection/connect` and `POST /connection/disconnect`; split `POST /shift-event` into `POST /shift/start` and `POST /shift/stop`. The action is now implied by the endpoint, not a `status` field.
- **Breaking:** Removed `status` from `ConnectionEvent` and `ShiftEvent`.
- **Breaking:** Renamed `ShiftEvent.android_id` to `ShiftEvent.id`.
- Added `ConnectionEvent.timestamp` (required) - when the connection or disconnection occurred on the device, per PO requirement.

## v1.0.0 - Initial version

- Initial release of Positioning Ingestion API contract
- Added ConnectionEvent and ShiftEvent schemas
- Added POST /connection-event and POST /shift-event endpoints
