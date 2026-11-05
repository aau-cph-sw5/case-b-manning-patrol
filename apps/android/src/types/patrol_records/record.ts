// the one place that describes what GET /api/v2/record sends. the wire schemas
// validate the snake_case payload from the patrol-record contract
// (contracts/api/v2/patrol-record) at the fetch boundary and map it to the
// camelCase types the rest of the app uses, like types/station.ts does for the
// dashboard stream. timestamps arrive as ISO strings over the wire, hence coerce.
import * as z from "zod";

const WireRecordAreaSchema = z.object({
  area_id: z.string(),
  name: z.string(),
  line: z.string().array(),
  station_id: z.string(),
  area_type: z.enum(["platform", "concourse"]),
});

export const RecordAreaSchema = WireRecordAreaSchema.transform((area) => ({
  areaId: area.area_id,
  name: area.name,
  line: area.line,
  stationId: area.station_id,
  areaType: area.area_type,
}));

const WireRecordSchema = z.object({
  android_id: z.uuid(),
  beacon_id: z.uuid(),
  started_at: z.coerce.date(),
  ended_at: z.coerce.date().nullable(),
  duration_secs: z.int().nullable(),
  min_patrol_duration_secs: z.int(),
  patrolled: z.boolean(),
  status: z.enum(["open", "closed"]),
  area: RecordAreaSchema,
});

export const RecordSchema = WireRecordSchema.transform((record) => ({
  androidId: record.android_id,
  beaconId: record.beacon_id,
  startedAt: record.started_at,
  endedAt: record.ended_at,
  durationSecs: record.duration_secs,
  minPatrolDurationSecs: record.min_patrol_duration_secs,
  patrolled: record.patrolled,
  status: record.status,
  area: record.area,
}));

export const RecordListSchema = z.object({
  records: RecordSchema.array(),
  time: z.coerce.date(),
});

export type RecordArea = z.infer<typeof RecordAreaSchema>;
export type Record = z.infer<typeof RecordSchema>;
export type RecordList = z.infer<typeof RecordListSchema>;
export type RecordStatus = Record["status"];
