import { useEffect, useState } from 'react'
import type { ApiStation } from '../data/stationsApi'
import type { Station } from '../data/stationView'
import { toStationCardData } from '../utils/stations'

const STATIONS_URL = 'http://localhost:8000/api/v2/stations'

export function useStations() {
  const [stations, setStations] = useState<Station[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(STATIONS_URL)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`API responded with status ${response.status}`)
        }
        return response.json() as Promise<ApiStation[]>
      })
      .then((data) => {
        // Map once when data arrives so lastPatrolAt is fixed for the
        // countdown; mapping during render would reset it every second.
        setStations(data.map(toStationCardData))
        setLoading(false)
      })
      .catch(() => {
        setError('Could not fetch stations from the API')
        setLoading(false)
      })
  }, [])

  return { stations, loading, error }
}
