import { describe, expect, it } from 'vitest'
import type { Dashboard } from './dashboardApi'
import { toViewStations } from './dashboardMapper'

const OVERDUE_AT = '2026-01-01T12:30:00Z'

function dashboard(areas: Partial<Dashboard['stations'][0]['areas'][0]>[]): Dashboard {
  return {
    stations: [
      {
        station_id: 'VAN',
        name: 'Vanløse',
        areas: areas.map((area, index) => ({
          area_id: `area-${index}`,
          name: 'Perron',
          line: 'M1 & M2',
          area_type: 'platform',
          covered_now: false,
          overdue_at: OVERDUE_AT,
          ...area,
        })),
      },
    ],
    trains: [],
    time: OVERDUE_AT,
  }
}

describe('toViewStations', () => {
  it('maps backend fields to the view model', () => {
    const [station] = toViewStations(
      dashboard([{ covered_now: true, overdue_at: null }]),
    )

    expect(station.stationId).toBe('VAN')
    expect(station.name).toBe('Vanløse')
    expect(station.levels[0]).toEqual({
      label: 'Perron',
      overdueAt: null,
      manned: true,
    })
  })

  it('parses overdue_at into epoch ms', () => {
    const [station] = toViewStations(
      dashboard([{ covered_now: false, overdue_at: OVERDUE_AT }]),
    )
    expect(station.levels[0].overdueAt).toBe(Date.parse(OVERDUE_AT))
  })

  it('numbers labels when a station has several areas of the same kind', () => {
    const [station] = toViewStations(
      dashboard([
        { area_type: 'platform' },
        { area_type: 'platform' },
        { area_type: 'concourse' },
      ]),
    )
    expect(station.levels.map((level) => level.label)).toEqual([
      'Perron 1',
      'Perron 2',
      'Forhal',
    ])
  })

  it('uses the plain label when the kind occurs once', () => {
    const [station] = toViewStations(dashboard([{ area_type: 'concourse' }]))
    expect(station.levels[0].label).toBe('Forhal')
  })
})
