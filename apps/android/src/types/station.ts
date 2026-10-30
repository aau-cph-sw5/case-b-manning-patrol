/**
 * The one place that describes what the backend datastream sends.
 *
 * The wire schema validates the snake_case payload from the
 * positioning-interface contract (contracts/api/v2/positioning-interface) at
 * the SSE boundary and maps it to the camelCase types the rest of the app
 * uses. Payload fields the app does not consume (station_id, trains, time)
 * are dropped by the parse. Line groups are a UI-only concept, so they live
 * here too.
 */
import * as z from "zod";

/** A pair of metro lines the steward app can filter stations by. */
export type LineGroup = "M1/M2" | "M3/M4";

/** Every line group, in the order the filter shows them. The first is the default. */
export const LINE_GROUPS: LineGroup[] = ["M1/M2", "M3/M4"];

/** One area as sent over SSE. `overdue_at` arrives as an ISO string, hence coerce. */
const WireAreaSchema = z.object({
  area_id: z.string(),
  name: z.string(),
  line: z.string().array(),
  area_type: z.enum(["platform", "concourse"]),
  covered_now: z.boolean(),
  overdue_at: z.coerce.date().nullable(),
});

/**
 * Validate one wire area and map it to camelCase.
 *
 * `overdueAt` is null while the area has no deadline yet.
 */
export const AreaSchema = WireAreaSchema.transform((area) => ({
  areaId: area.area_id,
  name: area.name,
  line: area.line,
  areaType: area.area_type,
  coveredNow: area.covered_now,
  overdueAt: area.overdue_at,
}));

export const StationSchema = z.object({
  name: z.string(),
  areas: AreaSchema.array(),
});

/** Validate one `dashboard` SSE payload: the full list of stations. */
export const StationOverviewSchema = z.object({
  stations: StationSchema.array(),
});

export type Area = z.infer<typeof AreaSchema>;
export type AreaType = Area["areaType"];
export type Station = z.infer<typeof StationSchema>;
export type StationOverview = z.infer<typeof StationOverviewSchema>;
