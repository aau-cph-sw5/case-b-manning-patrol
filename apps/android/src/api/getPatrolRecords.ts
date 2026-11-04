// fetches one steward's patrol records for the current shift, per
// contracts/api/v2/patrol-record: GET /api/v2/record?android_id={id}. the wire
// payload is validated against RecordListSchema at this boundary, so callers
// only ever see the camelCase RecordList type. resolves with the records once
// the server answers
// 200 and rejects otherwise, including when the server
// cannot be reached at all.
import { RecordListSchema, type RecordList } from "@/types/patrol_records/record";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

export async function getPatrolRecords(androidId: string): Promise<RecordList> {
  const url = `${API_BASE_URL}/api/v2/record?android_id=${encodeURIComponent(androidId)}`;

  console.log(`GET ${url}`);

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`the backend rejected the record request: ${response.status}`);
  }
  return RecordListSchema.parse(await response.json());
}
