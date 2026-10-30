// sample station data for the hook tests: realistic stations with deadlines
// generated relative to `now` so every run shows live counters and every risk
// state is represented: one overdue level, one due soon, a station being
// patrolled by another steward, and a station comfortably fresh.
import type { Area, AreaType, Station } from "@/types/station";

const MINUTE = 60_000;

export function createMockStations(now: number): Station[] {
  const at = (minutesFromNow: number) => new Date(now + minutesFromNow * MINUTE);

  const area = (
    areaType: AreaType,
    areaId: string,
    name: string,
    line: string,
    minutesTillOverdue: number,
    coveredNow = false,
  ): Area => ({
    areaId,
    name,
    line: [line],
    areaType,
    coveredNow,
    overdueAt: at(minutesTillOverdue),
  });

  return [
    {
      name: "Kongens Nytorv",
      areas: [
        area("platform", "kny-p", "Perron 1-2", "M1", -3),
        area("concourse", "kny-c", "Stationsområde", "M2", 42),
      ],
    },
    {
      name: "Frederiksberg",
      areas: [
        area("platform", "frb-p", "Perron", "M1", 37),
        area("concourse", "frb-c", "Stationsområde", "M3", 8),
      ],
    },
    {
      name: "Nørrebro",
      areas: [
        area("platform", "nor-p1", "Perron 1", "M3", 55),
        area("platform", "nor-p2", "Perron 2", "M3", 26),
        area("concourse", "nor-c", "Stationsområde", "M3", 61),
      ],
    },
    {
      name: "Islands Brygge",
      areas: [
        area("platform", "ibr-p", "Perron", "M1", 25, true),
        area("concourse", "ibr-c", "Stationsområde", "M2", 58),
      ],
    },
  ];
}
