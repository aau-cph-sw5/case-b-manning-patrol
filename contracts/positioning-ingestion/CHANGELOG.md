# Changelog



## v1.0.0 - Initial version

- Initial release of Positioning Ingestion API contract
- Added ConnectionEvent and ShiftEvent schemas
- Added POST /connection-event and POST /shift-event endpoints

## v1.0.0 - update

- **Breaking:** Split `POST /connection-event` into `POST /connection/connect` and `POST /connection/disconnect`; split `POST /shift-event` into `POST /shift/start` and `POST /shift/stop`. The action is now implied by the endpoint, not a `status` field.
- **Breaking:** Removed `status` from `ConnectionEvent` and `ShiftEvent`.
- **Breaking:** Renamed `ShiftEvent.android_id` to `ShiftEvent.id`.
- Added `ConnectionEvent.timestamp` (required) - when the connection or disconnection occurred on the device, per PO requirement.

## v2.0.0
- Updated naming of "shifts" to "patrol sessions"
- Add timestamp to the patrol-session-event
- Renamed schemas to kebab-case: `ConnectionEvent` -> `connection-event`, `PatrolSessionEvent` -> `patrol-session-event`