import './Legend.css'
import { useState } from 'react'
import { BsEmojiFrown, BsEmojiNeutral, BsEmojiSmile, BsPencil } from 'react-icons/bs';

interface LegendProps {
  attentionTime: number
  onAttentionTimeChange: (value: number) => void
}

interface LegendItem {
  color: string
  emoji: any
  label: string
  isEditable?: boolean
}

export default function Legend({ attentionTime, onAttentionTimeChange }: LegendProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState<string>(attentionTime.toString())

  const handleEditClick = () => {
    setEditValue(attentionTime.toString())
    setIsEditing(true)
  }

  const handleSave = () => {
    const numValue = parseInt(editValue, 10)
    if (!isNaN(numValue) && numValue >= 0) {
      onAttentionTimeChange(numValue)
    }
    setIsEditing(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSave()
    } else if (e.key === 'Escape') {
      setIsEditing(false)
    }
  }

  const ITEMS: LegendItem[] = [
    { color: 'text-green', emoji: BsEmojiSmile, label: 'Ok: fra 60 min.' },
    { 
      color: 'text-yellow', 
      emoji: BsEmojiNeutral, 
      label: isEditing ? 
        <input 
          type="number" 
          value={editValue} 
          onChange={(e) => setEditValue(e.target.value)} 
          onBlur={handleSave}
          onKeyDown={handleKeyDown}
          autoFocus
          className="edit-input"
        /> : `I risiko: fra ${attentionTime} min.`,
      isEditable: true
    },
    { color: 'text-red', emoji: BsEmojiFrown, label: 'Overskredet: 0 min.' },
  ]

  return (
    <div className="legend-box">
      {ITEMS.map((item) => (
        <div key={item.color} className="legend-item">
          <span className={item.color}>
            <item.emoji /> {item.label}
          </span>
          {item.isEditable && !isEditing && (
            <button className="edit-button" onClick={handleEditClick}>
              <BsPencil size={14} />
            </button>
          )}
        </div>
      ))}
    </div>
  )
}