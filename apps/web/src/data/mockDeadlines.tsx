const MIN = 60000; //ms
const shiftStart = Date.now();
//timestamp should be inserted into the spaces here, with VAN_Platform serving as a clarification example
export const LEVEL_DEADLINES: Record<string, number> = {
  //'VAN_Platform': 1792672588507,
  'VAN_Platform': shiftStart + 60 * MIN,
  'FLT_Platform': shiftStart + 6 * MIN,
  'FLT_Concourse': shiftStart - 5 * MIN,
  'LIN_Platform': shiftStart + 60 * MIN,
  'LIN_Concourse': shiftStart + 45 * MIN,
  'FAS_Platform': shiftStart + 49 * MIN,
  'FAS_Concourse': shiftStart + 31 * MIN,
  'KNG_Platform1': shiftStart + 19 * MIN,
  'KNG_Platform2': shiftStart + 10 * MIN,
  'KNG_Concourse': shiftStart + 13 * MIN,
};
