import './Legend.css'
import { AttentionTime } from '../settings.ts'

interface LegendItem {
  color: string
  emoji: string
  label: string
}

const ITEMS: LegendItem[] = [
  { color: 'text-green', emoji: '😊', label: 'Ok: fra 60 min.' },
  { color: 'text-yellow', emoji: '😐', label: `I risiko: fra ${AttentionTime} min.` },
  { color: 'text-red', emoji: '😞', label: 'Overskredet: 0 min.' },
]

export default function Legend() {
  return (
    <div className="legend-box">
      {ITEMS.map((item) => (
        <div key={item.color} className="legend-item">
          <span className={item.color}>{item.emoji} {item.label}</span>
        </div>
      ))}
    </div>
  )
}