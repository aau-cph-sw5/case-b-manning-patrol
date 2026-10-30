/** One minute in milliseconds. */
const MIN = 60000;
const shiftStart = Date.now();
/**
 * Mock patrol deadline per level, in ms since epoch, keyed
 * `${stationCode}_${level.label}`.
 *
 * Stands in for deadlines from the backend. The values are offsets from the
 * moment the module loads; a fixed deadline is a plain timestamp instead,
 * e.g. `'VAN_Perron': 1792672588507`.
 */
export const LEVEL_DEADLINES: Record<string, number> = {
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
