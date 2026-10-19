const MIN = 60000 //ms
const shiftStart = Date.now() 
export interface StationLevel {
  label: string
  lastPatrolAt: number
  manned: boolean
}

export interface Station {
  code: string
  name: string
  levels: StationLevel[]
}


export const STATIONS: Station[] = [
  {
    code: 'VAN',
    name: 'Vanløse',
    levels: [{ label: 'Platform', lastPatrolAt: shiftStart, manned: false }],
  },
  {
    code: 'FLT',
    name: 'Flintholm',
    levels: [
      { label: 'Platform', lastPatrolAt: Date.now() - 54 * MIN, manned: false },
      { label: 'Concourse', lastPatrolAt: Date.now() - 65 * MIN, manned: false },
    ],
  },
  {
    code: 'LIN',
    name: 'Lindevang',
    levels: [
      { label: 'Platform', lastPatrolAt: Date.now(), manned: true },
      { label: 'Concourse', lastPatrolAt: Date.now() - 15 * MIN, manned: false },
    ],
  },
  {
    code: 'FAS',
    name: 'Fasanvej',
    levels: [
      { label: 'Platform', lastPatrolAt: Date.now() - 11 * MIN, manned: false },
      { label: 'Concourse', lastPatrolAt: Date.now() - 29 * MIN, manned: false },
    ],
  },
  {
    code: 'KNG',
    name: 'Kongens',
    levels: [
      { label: 'Platform1', lastPatrolAt: Date.now() - 41 * MIN, manned: false },
      { label: 'Platform2', lastPatrolAt: Date.now() - 50 * MIN, manned: false },
      { label: 'Concourse', lastPatrolAt: Date.now() - 37 * MIN, manned: false },
    ],
  },
]
