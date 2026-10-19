export interface StationLevel {
  label: string
  beaconId: string
  lastPatrolAt: number
  manned: boolean
}

export interface Station {
  code: string
  name: string
  levels: StationLevel[]
}

