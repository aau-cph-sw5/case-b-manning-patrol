export type LineGroup = "M1/M2" | "M3/M4";

export const LINE_GROUPS: LineGroup[] = ["M1/M2", "M3/M4"];

export type AreaType = "Platform" | "Concourse";

export type Area = {
  type: AreaType;
  timeTillOverdue: number;
  line: string;
  name: string;
  coveredNow: boolean;
};

export type StationRecord = {
  id?: string;
  routeCodes?: string[];
  name: string;
  areas: Area[];
};
