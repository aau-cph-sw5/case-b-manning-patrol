/**
 * The at-risk threshold as the dashboard stream sends it.
 *
 * The wire schema validates the snake_case payload of an `at-risk-threshold`
 * event from the positioning-interface contract
 * (contracts/api/v2/positioning-interface) at the SSE boundary and maps it to
 * the camelCase type the rest of the app uses.
 */
import * as z from "zod";

/** The backend's default, used until the first `at-risk-threshold` event arrives. */
export const DEFAULT_AT_RISK_THRESHOLD_MINUTES = 10;

/** Validate the data of one `at-risk-threshold` event and map it to camelCase. */
export const AtRiskThresholdSchema = z
  .object({
    at_risk_threshold_minutes: z.number().int().min(1),
  })
  .transform((threshold) => ({
    atRiskThresholdMinutes: threshold.at_risk_threshold_minutes,
  }));

/** The at-risk threshold: minutes before `overdueAt` at which an area counts as due. */
export type AtRiskThreshold = z.infer<typeof AtRiskThresholdSchema>;
