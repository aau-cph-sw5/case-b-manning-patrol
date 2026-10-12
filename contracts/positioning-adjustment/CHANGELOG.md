# Changelog

## v0.1.0 - Initial draft (unpublished)

- Draft of Adjustment Event API contract for group review. Not yet published.
- `POST /api/v1/adjustment` appends a manual correction to the append-only
  event store; there is no update or delete path.
- `AdjustmentEventCreate` request: `actor`, optional `target_event_id` (an
  adjustment may point at another adjustment), a `corrected_fact` in the same
  vocabulary as the ingestion events, and the mandatory `reason` and `author`
  audit fields.
- `AdjustmentEventStored` response: all request fields plus the
  server-generated `adjustment_id`, `server_timestamp`, and `source` — the
  server-assigned origin of the write, never taken from the request body.
