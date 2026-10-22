// This serves the mock fixture; when the real endpoint lands, only this file
// changes and the rest of the app should pick it up - Delete comment when endpoint is made.
import { createMockStations } from "@/fixtures/mockStations";
import type { StationRecord } from "@/types/station";

export type StationsSnapshot = {
  stations: StationRecord[];
  lastUpdatedAt: number;
};

export async function fetchStations(): Promise<StationsSnapshot> {
  return { stations: createMockStations(Date.now()), lastUpdatedAt: Date.now() };
}
