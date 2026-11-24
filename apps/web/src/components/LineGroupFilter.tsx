import './LineGroupFilter.css'

import {
  LINE_GROUP_SELECTIONS,
  ROUTE_COLORS,
  selectionRoutes,
  type LineGroupSelection,
} from '../utils/lineGroup'

interface LineGroupFilterProps {
  selected: LineGroupSelection
  onSelect: (selection: LineGroupSelection) => void
}

/**
 * Segmented Alle | M1/M2 | M3/M4 toggle, mirrors the Android StationFilter
 * with an extra first segment for the composed all-lines view. The 'ALL'
 * segment is a plain text label; the group segments show their route badges.
 */
export default function LineGroupFilter({ selected, onSelect }: LineGroupFilterProps) {
  const selectedIndex = LINE_GROUP_SELECTIONS.indexOf(selected)

  return (
    <div className="line-filter" role="tablist" aria-label="Filtrer efter metrolinje">
      <span
        className="line-filter-thumb"
        style={{ transform: `translateX(${selectedIndex * 100}%)` }}
      />
      {LINE_GROUP_SELECTIONS.map((selection) => (
        <button
          key={selection}
          type="button"
          role="tab"
          aria-selected={selected === selection}
          className={`line-filter-segment${selected === selection ? ' selected' : ''}`}
          onClick={() => onSelect(selection)}
        >
          {selection === 'ALL' ? (
            <span className="line-filter-all-label">Alle</span>
          ) : (
            selectionRoutes(selection).map((route) => (
              <span
                key={route}
                className="route-badge"
                style={{
                  backgroundColor: ROUTE_COLORS[route] ?? '#686868',
                  color: route === 'M2' ? '#000000' : '#ffffff',
                }}
              >
                {route}
              </span>
            ))
          )}
        </button>
      ))}
    </div>
  )
}
