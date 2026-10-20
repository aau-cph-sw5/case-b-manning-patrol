import * as z from "zod";


export const AreaSchema = z.object({
    areaId: z.string(),
    name: z.string(),
    line: z.string(),
    areaType: z.enum(["platform", "concourse"]),
    status: z.enum(["compliant", "overdue"]),
    coveredNow: z.boolean(),
    overdueAt: z.date().nullable(),
})

export const StationSchema = z.object({
    name: z.string(),
    areas: AreaSchema.array(),
})

export const StationOverviewSchema = z.object({
    stations: StationSchema.array(),
})

export type Area = z.infer<typeof AreaSchema>;
export type Station = z.infer<typeof StationSchema>;
export type StationOverview = z.infer<typeof StationOverviewSchema>;



