// mock "stations due for patrol" data for the figma template screen. the seeded minutes
// stand in for "time since this station was last patrolled" until the backend serves
// the real values.
export type MetroLine = "M1" | "M2" | "M3" | "M4";

export type Station = {
  name: string;
  lines: MetroLine[];
  // seconds since the last patrol when the screen opens
  initialSeconds: number;
};

export type StationMode = "m1/m2" | "m3/m4";

export const MODE_LINES: Record<StationMode, MetroLine[]> = {
  "m1/m2": ["M1", "M2"],
  "m3/m4": ["M3", "M4"],
};

const stationData: { name: string; lines: MetroLine[] }[] = [
  { name: "Nørreport", lines: ["M1", "M2", "M3"] },
  { name: "Forum", lines: ["M1", "M2"] },
  { name: "Kongens Nytorv", lines: ["M1", "M2", "M3", "M4"] },
  { name: "Christianshavn", lines: ["M1", "M2"] },
  { name: "Vanløse", lines: ["M1", "M2"] },
  { name: "Flintholm", lines: ["M1", "M2"] },
  { name: "Lindevang", lines: ["M1", "M2"] },
  { name: "Fasanvej", lines: ["M1", "M2"] },
  { name: "Frederiksberg", lines: ["M1", "M2", "M3"] },
  { name: "Nuuks Plads", lines: ["M3"] },
  { name: "Aksel Møllers Have", lines: ["M3"] },
  { name: "Frederiksberg Allé", lines: ["M3"] },
  { name: "Enghave Plads", lines: ["M3"] },
  { name: "København H", lines: ["M3", "M4"] },
  { name: "Rådhuspladsen", lines: ["M3", "M4"] },
  { name: "Gammel Strand", lines: ["M3", "M4"] },
  { name: "Marmorkirken", lines: ["M3", "M4"] },
  { name: "Østerport", lines: ["M3", "M4"] },
  { name: "Trianglen", lines: ["M3"] },
  { name: "Poul Henningsens Plads", lines: ["M3"] },
  { name: "Vibenshus Runddel", lines: ["M3"] },
  { name: "Skjolds Plads", lines: ["M3"] },
  { name: "Nørrebros Runddel", lines: ["M3"] },
  { name: "Nørrebro", lines: ["M3"] },
  { name: "Nordhavn", lines: ["M4"] },
];

const startingMinutes = [
  8, 32, 47, 18, 52, 26, 41, 12, 56, 37, 23, 49, 15, 34, 44, 7, 51, 29, 39, 11, 46, 21, 58,
  31, 17,
];

export const stations: Station[] = stationData.map((station, index) => ({
  name: station.name,
  lines: station.lines,
  initialSeconds: startingMinutes[index] * 60 + ((index * 13) % 60),
}));
