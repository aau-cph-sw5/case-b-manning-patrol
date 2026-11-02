import './LineGroupFilter.css'

import {
  LINE_GROUPS,
  LINE_GROUP_ROUTES,
  ROUTE_COLORS,
  type LineGroup,
} from '../utils/lineGroup'

interface LineGroupFilterProps {
  selected: LineGroup
  onSelect: (lineGroup: LineGroup) => void
}

// segmented M1/M2 | M3/M4 toggle, mirrors the Android StationFilter
export default function LineGroupFilter({ selected, onSelect }: LineGroupFilterProps) {
  const selectedIndex = LINE_GROUPS.indexOf(selected)

  return (
    <div className="line-filter" role="tablist" aria-label="Filtrer efter metrolinje">
      <span
        className="line-filter-thumb"
        style={{ transform: `translateX(${selectedIndex * 100}%)` }}
      />
      {LINE_GROUPS.map((lineGroup) => (
        <button
          key={lineGroup}
          type="button"
          role="tab"
          aria-selected={selected === lineGroup}
          className={`line-filter-segment${selected === lineGroup ? ' selected' : ''}`}
          onClick={() => onSelect(lineGroup)}
        >
          {LINE_GROUP_ROUTES[lineGroup].map((route) => (
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
          ))}
        </button>
      ))}
    </div>
  )
}
