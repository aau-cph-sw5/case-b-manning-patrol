# Changelog

## v0.1.0 - Initial draft (unpublished)

- Draft of Adjustment Event API contract for group review. Not yet published.
- Added `POST /api/v1/adjustments` endpoint.
- Added `AdjustmentEventCreate` schema: `void` (skip a target event in
  projections) and `compensate` (record a `CorrectedFact`) variants,
  discriminated by `adjustment_type`.
- Added mandatory `reason` and `author` audit fields and a `source` enum per
  the append-only store acceptance criteria.

## v0.1.0 - Simplified draft (unpublished)

- Renamed endpoint to `POST /api/v1/adjustment`.
- Simplified `AdjustmentEventCreate` to a single model: removed the
  `void`/`compensate` variants, `adjustment_type` discriminator, and
  `target_event_id`; a correction is now always expressed as a
  `corrected_fact`.
- Removed the `source` request field; the write origin is no longer part of
  the request body.
- Re-added optional `target_event_id` on `AdjustmentEventCreate`: an adjustment
  may point at another adjustment, so adjustments can themselves be adjusted.
