// the mock broadcast array until the backend datastream exists (PBI 009 notes).
// deadlines are generated relative to `now` so every run shows live counters and
// every risk state is represented: one overdue level, one due soon, a station
// being patrolled by another steward, and a station comfortably fresh.
import type { Area, AreaType, StationRecord } from "@/types/station";

const MINUTE = 60_000;

export function createMockStations(now: number): StationRecord[] {
  const at = (minutesFromNow: number) => now + minutesFromNow * MINUTE;

  const area = (
    type: AreaType,
    name: string,
    line: string,
    minutesTillOverdue: number,
    coveredNow = false,
  ): Area => ({
    type,
    name,
    line,
    timeTillOverdue: at(minutesTillOverdue),
    coveredNow,
  });

  return [
    {
      name: "Kongens Nytorv",
      routeCodes: ["M1", "M2"],
      areas: [
        area("Platform", "Perron 1-2", "M1", -3),
        area("Concourse", "Stationsområde", "M2", 42),
      ],
    },
    {
      name: "Frederiksberg",
      routeCodes: ["M1", "M2", "M3", "M4"],
      areas: [
        area("Platform", "Perron", "M1", 37),
        area("Concourse", "Stationsområde", "M3", 8),
      ],
    },
    {
      name: "Nørrebro",
      routeCodes: ["M3", "M4"],
      areas: [
        area("Platform", "Perron 1", "M3", 55),
        area("Platform", "Perron 2", "M3", 26),
        area("Concourse", "Stationsområde", "M3", 61),
      ],
    },
    {
      name: "Islands Brygge",
      routeCodes: ["M1", "M2"],
      areas: [
        area("Platform", "Perron", "M1", 25, true),
        area("Concourse", "Stationsområde", "M2", 58),
      ],
    },
  ];
}
