/** Colour legend for the dashboard, with an inline editor for the at-risk threshold. */
import './Legend.css'
import { useState } from 'react'
import { BsEmojiFrown, BsEmojiNeutral, BsEmojiSmile, BsPencil } from 'react-icons/bs';

interface LegendProps {
  /** Current at-risk threshold in minutes. */
  riskTime: number
  /** Called when an edit is saved, only with a whole number of at least 1. */
  onRiskTimeChange: (value: number) => void
}

interface LegendItem {
  color: string
  emoji: any
  label: React.ReactNode
  isEditable?: boolean
}

/**
 * Render the three colour states: ok, at risk and overdue.
 *
 * The pencil on the at-risk row opens a number input; Enter or leaving the
 * field saves, Escape cancels. Input that does not parse to a number of at
 * least 1 is dropped without a message, and decimals are cut off. The "ok"
 * label always says 60 minutes, whatever the threshold.
 */
export default function Legend({ riskTime, onRiskTimeChange }: LegendProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState<string>(riskTime.toString())

  const handleEditClick = () => {
    setEditValue(riskTime.toString())
    setIsEditing(true)
  }

  const handleSave = () => {
    const numValue = parseInt(editValue, 10)
    if (!isNaN(numValue) && numValue >= 1) {
      onRiskTimeChange(numValue)
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
          min={1}
          value={editValue} 
          onChange={(e) => setEditValue(e.target.value)} 
          onBlur={handleSave}
          onKeyDown={handleKeyDown}
          autoFocus
          className="edit-input"
        /> : `I risiko: fra ${riskTime} min.`,
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
