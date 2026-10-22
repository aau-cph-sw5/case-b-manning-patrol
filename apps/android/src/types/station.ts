export type StationRecord = {
  id: string;
  name: string;
  subtitle?: string;
  routeCodes?: string[];
};

export const LINE_GROUPS = ["M1/M2", "M3/M4"] as const;
export type LineGroup = (typeof LINE_GROUPS)[number];
