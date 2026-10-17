export interface StationLevel {
  label: string
  value: string
}

export interface Station {
  code: string
  name: string
  person?: boolean
  levels: StationLevel[]
}

export interface AttentionItem {
  code: string
  value: string
  person?: boolean
}

export const STATIONS: Station[] = [
  {
    code: 'VAN',
    name: 'Vanløse',
    levels: [{ label: 'Platform', value: '10 min' }],
  },
  {
    code: 'FLT',
    name: 'Flintholm',
    person: true,
    levels: [
      { label: 'Platform', value: '6 min' },
      { label: 'Concourse', value: '+5 min' },
    ],
  },
  {
    code: 'LIN',
    name: 'Lindevang',
    levels: [
      { label: 'Platform', value: '48 min' },
      { label: 'Concourse', value: '45 min' },
    ],
  },
  {
    code: 'FAS',
    name: 'Fasanvej',
    levels: [
      { label: 'Platform', value: '49 min' },
      { label: 'Concourse', value: '31 min' },
    ],
  },
  {
    code: 'KNG',
    name: 'Kongens',
    levels: [
      { label: 'Platform1', value: '19 min' },
      { label: 'Platform2', value: '10 min' },
      { label: 'Concourse', value: '23 min' },
    ],
  },
]

export const ATTENTION: AttentionItem[] = [
  { code: 'FLT_CON', value: '+5 min' },
  { code: 'FLT_PLAT', value: '6 min', person: true },
  { code: 'VAN_PLAT', value: '10 min' },
  { code: 'KNG_PLAT2', value: '10 min' },
]