const MIN = 60000; //ms
const shiftStart = Date.now();
//timestamp should be inserted into the spaces here, with VAN_Perron serving as a clarification example
export const LEVEL_DEADLINES: Record<string, number> = {
  //'VAN_Perron': 1792672588507,
  'VAN_Perron': shiftStart + 60 * MIN,
  'FLT_Perron': shiftStart + 6 * MIN,
  'FLT_Forhal': shiftStart - 5 * MIN,
  'LIN_Perron': shiftStart + 60 * MIN,
  'LIN_Forhal': shiftStart + 45 * MIN,
  'FAS_Perron': shiftStart + 49 * MIN,
  'FAS_Forhal': shiftStart + 31 * MIN,
  'KNG_Perron 1': shiftStart + 19 * MIN,
  'KNG_Perron 2': shiftStart + 10 * MIN,
  'KNG_Forhal': shiftStart + 13 * MIN,
};
