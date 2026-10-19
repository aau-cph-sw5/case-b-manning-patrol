import { AttentionTime } from "../settings"

export type TimeColor = 'row-green' | 'row-yellow' | 'row-red'

export function timeColorClass(value: string): TimeColor {
  if (value.startsWith('+')) {
    return 'row-red'
  }
  const minutes = Number.parseFloat(value)
  return minutes > AttentionTime ? 'row-green' : 'row-yellow'
}

export default timeColorClass