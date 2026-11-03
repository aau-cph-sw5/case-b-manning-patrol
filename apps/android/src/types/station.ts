/**
 * The one place that describes what the backend datastream sends.
 *
 * The wire schema validates the snake_case payload from the
 * positioning-interface contract (contracts/api/v2/positioning-interface) at
 * the SSE boundary and maps it to the camelCase types the rest of the app
 * uses. Payload fields the app does not consume (station_id, trains, time) are
 * dropped by the parse. Line groups are a UI-only concept, so they live here
 * too.
 */
import * as z from "zod";

/** A pair of metro lines the steward filters the station list by. */
export type LineGroup = "M1/M2" | "M3/M4";

/** Line groups in the order the filter shows them; the first is the default. */
export const LINE_GROUPS: LineGroup[] = ["M1/M2", "M3/M4"];

/** An area as the stream sends it. overdue_at arrives as an ISO string over SSE, hence coerce. */
const WireAreaSchema = z.object({
  area_id: z.string(),
  name: z.string(),
  line: z.string().array(),
  area_type: z.enum(["platform", "concourse"]),
  covered_now: z.boolean(),
  overdue_at: z.coerce.date().nullable(),
});

/** Validate one wire area and map it to an {@link Area}. */
export const AreaSchema = WireAreaSchema.transform((area) => ({
  areaId: area.area_id,
  name: area.name,
  line: area.line,
  areaType: area.area_type,
  coveredNow: area.covered_now,
  overdueAt: area.overdue_at,
}));

/** Validate one station; its station_id is dropped. */
export const StationSchema = z.object({
  name: z.string(),
  areas: AreaSchema.array(),
});

/** Validate the data of one `dashboard` event; trains and time are dropped. */
export const StationOverviewSchema = z.object({
  stations: StationSchema.array(),
});

/**
 * A patrol area (a platform or concourse level) of a station.
 *
 * `overdueAt` is the deadline for the next patrol. The contract sends null
 * while the area is covered right now and when it has never been patrolled.
 */
export type Area = z.infer<typeof AreaSchema>;
/** Kind of area; the backend uses it to decide how long a visit must last to count. */
export type AreaType = Area["areaType"];
/** A station with its patrol areas. */
export type Station = z.infer<typeof StationSchema>;
/** Everything the app keeps from one `dashboard` event: the stations. */
export type StationOverview = z.infer<typeof StationOverviewSchema>;
