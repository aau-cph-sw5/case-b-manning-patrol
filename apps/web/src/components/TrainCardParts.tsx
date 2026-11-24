/**
 * Presentational parts of the train manning card: route badges, trend
 * arrows and the card shown when the trains stream failed before any data
 * arrived.
 */
import { BsArrowDown, BsArrowRight, BsArrowUp } from 'react-icons/bs'

import { LINE_GROUPS, LINE_GROUP_ROUTES, ROUTE_COLORS } from '../utils/lineGroup.ts'
import type { Trend } from '../utils/trainManning.ts'

/** Render one badge per metro line, coloured like on the Android app. */
export function RouteBadges({ routes }: { routes: string[] }) {
  return (
    <span className="route-badges">
      {routes.map((route) => (
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
    </span>
  )
}

/** Render an arrow showing the trend direction, or nothing when there is none. */
export function TrendArrow({ trend, label }: { trend: Trend | null; label: string }) {
  if (trend === null) return null
  const Icon = trend === 'up' ? BsArrowUp : trend === 'down' ? BsArrowDown : BsArrowRight
  const cls = trend === 'up' ? 'ok-arrow' : trend === 'down' ? 'low-arrow' : 'flat-arrow'
  const text = trend === 'up' ? 'stigende' : trend === 'down' ? 'faldende' : 'stabil'
  return <Icon className={cls} aria-label={`${label} ${text}`} />
}

/**
 * Render the card shown when the trains stream errored before any data
 * arrived: all line badges and a "—" figure, plus a message that no manning
 * data is available.
 */
export function NoManningData() {
  return (
    <section className="card train-card">
      <header className="train-card-head">
        <h2>
          <RouteBadges routes={LINE_GROUPS.flatMap((group) => LINE_GROUP_ROUTES[group])} />
        </h2>
        <span className="train-head-status">
          <span className="train-head-pct">—</span>
        </span>
      </header>
      <p className="train-empty" role="status">
        Ingen bemandingsdata tilgængelig — tjek forbindelsen til serveren
      </p>
    </section>
  )
}
