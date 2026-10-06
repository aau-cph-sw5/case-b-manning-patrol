# Changelog

## v0.1.0 - Initial draft (unpublished)

- Draft of Adjustment Event API contract for group review. Not yet published.
- Added `POST /api/v1/adjustments` endpoint.
- Added `AdjustmentEventCreate` schema: `void` (skip a target event in
  projections) and `compensate` (record a `CorrectedFact`) variants,
  discriminated by `adjustment_type`.
- Added mandatory `reason` and `author` audit fields and a `source` enum per
  the append-only store acceptance criteria.
