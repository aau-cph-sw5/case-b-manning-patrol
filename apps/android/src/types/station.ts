export type AreaType = "Platform" | "Concourse";

export type Area = {
  type: AreaType;
  timeTillOverdue: number;
  line: string;
  name: string;
  coveredNow: boolean;
};

export type StationRecord = {
  name: string;
  areas: Area[];
};
