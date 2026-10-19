import type { StationRecord } from "@/types/station";

export const MOCK_STATIONS: StationRecord[] = [
  {
    id: "frederiksberg",
    name: "Frederiksberg",
    subtitle: "Perron og stationsområde",
    routeCodes: ["M1", "M2", "M3"],
  },
  {
    id: "kongens-nytorv",
    name: "Kongens Nytorv",
    subtitle: "Perron og stationsområde",
    routeCodes: ["M1", "M2", "M3"],
  },
  {
    id: "norrebro",
    name: "Nørrebro",
    subtitle: "Perron og stationsområde",
    routeCodes: ["M3"],
  },
];