export function timeColorClass(value: string): string {
  if (value.startsWith('+')) {
    return 'row-red'
  }
  const minutes = Number.parseFloat(value)
  return minutes > 10 ? 'row-green' : 'row-yellow'
}

export default timeColorClass