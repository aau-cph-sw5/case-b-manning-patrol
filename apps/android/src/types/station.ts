// the one place that describes what the backend datastream sends. the zod
// schemas validate at the SSE boundary; the exported types flow through the
// rest of the app. line groups are a UI-only concept, so they live here too.
import * as z from "zod";

export type LineGroup = "M1/M2" | "M3/M4";

export const LINE_GROUPS: LineGroup[] = ["M1/M2", "M3/M4"];

// overdueAt arrives as an ISO string over SSE, hence coerce.
export const AreaSchema = z.object({
  areaId: z.string(),
  name: z.string(),
  line: z.string(),
  areaType: z.enum(["platform", "concourse"]),
  status: z.enum(["compliant", "overdue"]),
  coveredNow: z.boolean(),
  overdueAt: z.coerce.date().nullable(),
});

export const StationSchema = z.object({
  name: z.string(),
  areas: AreaSchema.array(),
});

export const StationOverviewSchema = z.object({
  stations: StationSchema.array(),
});

export type Area = z.infer<typeof AreaSchema>;
export type AreaType = Area["areaType"];
export type Station = z.infer<typeof StationSchema>;
export type StationOverview = z.infer<typeof StationOverviewSchema>;
