import './DateSelector.css'

type DateSelectorProps = {
  value: string
  maxDate: string
  onDateChange: (date: string) => void
}

export default function DateSelector({
  value,
  maxDate,
  onDateChange,
}: DateSelectorProps) {
  return (
    <label className="date-selector">
      <span>Vis oversigt for:</span>
      <input
        className="date-selector__input"
        type="date"
        value={value}
        max={maxDate}
        onChange={(event) => onDateChange(event.currentTarget.value)}
      />
    </label>
  )
}