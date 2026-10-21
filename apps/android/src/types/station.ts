export type StationRecord = {
  id: string;
  name: string;
  subtitle?: string;
  routeCodes?: string[];
};

// line groups the metro runs its stations in. interchange stations have one platform
// per group (kongens nytorv has an M1/M2 perron and an M3/M4 perron), so the backend
// tags every area with the group it serves.
export const LINE_GROUPS = ["M1/M2", "M3/M4"] as const;
export type LineGroup = (typeof LINE_GROUPS)[number];
