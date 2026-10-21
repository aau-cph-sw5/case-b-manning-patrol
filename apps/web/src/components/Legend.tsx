import './Legend.css'
import { AttentionTime } from '../settings.ts'
import { BsEmojiFrown, BsEmojiNeutral, BsEmojiSmile } from 'react-icons/bs';
import type { IconType } from 'react-icons/lib';


interface LegendItem {
  color: string
  emoji: IconType
  label: string
}

const ITEMS: LegendItem[] = [
  { color: 'text-green', emoji: BsEmojiSmile , label: 'Ok: fra 60 min.' },
  { color: 'text-yellow', emoji: BsEmojiNeutral, label: `I risiko: fra ${AttentionTime} min.` },
  { color: 'text-red', emoji: BsEmojiFrown, label: 'Overskredet: 0 min.' },
]

export default function Legend() {
  return (
    <div className="legend-box">
      {ITEMS.map((item) => (
        <div key={item.color} className="legend-item">
          <span className={item.color}><item.emoji/> {item.label}</span>
        </div>
      ))}
    </div>
  )
}