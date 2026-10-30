/** One minute in milliseconds. */
const MIN = 60000
const shiftStart = Date.now()
/** One patrolled area of a station, e.g. a platform or the concourse. */
export interface StationLevel {
  /** Display name, also used in the `LEVEL_DEADLINES` key. */
  label: string
  /** Time of the last patrol in ms since epoch. Not read by the dashboard. */
  lastPatrolAt: number
  /** A steward is on the level right now, so its countdown is paused. */
  manned: boolean
}

/** A station on the dashboard and its patrolled levels. */
export interface Station {
  code: string
  name: string
  levels: StationLevel[]
}


/**
 * Mock stations the dashboard shows until it reads them from the backend.
 *
 * Timestamps are computed once when the module loads, not per render.
 */
export const STATIONS: Station[] = [
  {
    code: 'VAN',
    name: 'Vanløse',
    levels: [{ label: 'Perron', lastPatrolAt: shiftStart, manned: false }],
  },
  {
    code: 'FLT',
    name: 'Flintholm',
    levels: [
      { label: 'Perron', lastPatrolAt: Date.now() - 54 * MIN, manned: false },
      { label: 'Forhal', lastPatrolAt: Date.now() - 65 * MIN, manned: false },
    ],
  },
  {
    code: 'LIN',
    name: 'Lindevang',
    levels: [
      { label: 'Perron', lastPatrolAt: Date.now(), manned: true },
      { label: 'Forhal', lastPatrolAt: Date.now() - 15 * MIN, manned: false },
    ],
  },
  {
    code: 'FAS',
    name: 'Fasanvej',
    levels: [
      { label: 'Perron', lastPatrolAt: Date.now() - 11 * MIN, manned: false },
      { label: 'Forhal', lastPatrolAt: Date.now() - 29 * MIN, manned: false },
    ],
  },
  {
    code: 'KNG',
    name: 'Kongens',
    levels: [
      { label: 'Perron 1', lastPatrolAt: Date.now() - 41 * MIN, manned: false },
      { label: 'Perron 2', lastPatrolAt: Date.now() - 50 * MIN, manned: false },
      { label: 'Forhal', lastPatrolAt: Date.now() - 37 * MIN, manned: false },
    ],
  },
]
