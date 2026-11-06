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

/**
 * A connection the phone has confirmed but the backend has not acknowledged
 * yet (patrol-record contract: while the connect/disconnect POST is in
 * flight or has failed, the client's local state is the source of origin).
 *
 * Client-only placeholder: it carries no `area`, because the backend resolves
 * the beacon's area and the frontend has no reference sheet. It matches a
 * server `Record` on `beaconId` + `startedAt`, since the server stamps
 * `started_at` from the connect event's own device timestamp.
 */
export type PendingRecord = {
  beaconId: string;
  /** When the confirmed connect happened on the device. */
  startedAt: Date;
  /** Set when the disconnect was confirmed locally; null while still connected. */
  endedAt: Date | null;
  /** "open" until the disconnect is confirmed, then "closed" — drives the history section. */
  status: RecordStatus;
  /** Always true; narrows a {@link HistoryEntry} down to the placeholder. */
  pending: true;
};

/** One row of the patrol history: a server record or a client-side pending placeholder. */
export type HistoryEntry = Record | PendingRecord;

/** Return whether a history entry is a pending placeholder rather than a server record. */
export function isPendingRecord(entry: HistoryEntry): entry is PendingRecord {
  return "pending" in entry;
}
