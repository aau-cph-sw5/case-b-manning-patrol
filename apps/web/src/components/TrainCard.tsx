/**
 * Dashboard card showing train manning from the trains SSE stream: the share
 * of running time trains were manned for the selected scope (all lines, or
 * one line group) against the 70% compliance target.
 *
 * The card is a summary row — route badges and the manned count on the left,
 * percentage, trend and a slim progress bar on the right. When a single line
 * group is selected, a head with the overall percentage and a full-width bar
 * is shown below it, since those differ from the group figures; for 'ALL' the
 * head is hidden because the summary already shows the overall figures.
 */

import type { TrainsUpdate } from '../api/dashboardApi'

import { BsArrowDown, BsArrowRight, BsArrowUp } from 'react-icons/bs'

import {
  ALL_ROUTES,
  LINE_GROUP_ROUTES,
  ROUTE_COLORS,
  type LineGroupSelection,
} from '../utils/lineGroup.ts'

/** Compliance rule: a train must be manned at least 70% of its running time. */
const MANNING_TARGET_PCT = 70

/** Shown until the first trains event arrives, so the card renders its placeholder. */
const EMPTY_UPDATE: TrainsUpdate = {
  trains: [],
  manning_percent: null,
  m1m2_manning_percent: null,
  m3m4_manning_percent: null,
  time: '',
}

/** Round a backend percentage (0..100) to a whole percent; null means no running time. */
function pct(percent: number | null): number | null {
  return percent === null ? null : Math.round(percent)
}

function RouteBadges({ routes }: { routes: string[] }) {
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

type Trend = 'up' | 'down' | 'flat'

/** Percentage points within which the current manned share counts as flat. */
const TREND_TOLERANCE_PCT = 1

/**
 * Direction the manning percentage is heading right now.
 *
 * The percentage is manned time over running time, so it rises while the share
 * of trains manned right now is above it and falls while it is below. Within
 * {@link TREND_TOLERANCE_PCT} of it the trend is flat.
 *
 * @param percent - The displayed manning percentage (0..100).
 * @returns Null when there are no trains or no percentage yet.
 */
function trendOf(manned: number, total: number, percent: number | null): Trend | null {
  if (total <= 0 || percent === null) return null
  const currentPct = (manned / total) * 100
  if (currentPct > percent + TREND_TOLERANCE_PCT) return 'up'
  if (currentPct < percent - TREND_TOLERANCE_PCT) return 'down'
  return 'flat'
}

function TrendArrow({ trend, label }: { trend: Trend | null; label: string }) {
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
function NoManningData() {
  return (
    <section className="card train-card">
      <header className="train-card-head">
        <h2>
          <RouteBadges routes={ALL_ROUTES} />
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

/**
 * Render the manning summary for the selected scope: every train for 'ALL',
 * or only the trains serving the selected line group. For a single line
 * group the overall head and bar are rendered below the summary; for 'ALL'
 * they are omitted, since the summary already shows the overall figures.
 *
 * @param update - Latest trains stream event; null before the first one. Null
 *   without an error renders the loading placeholder, the same as a stream
 *   with no trains; null together with `error` renders {@link NoManningData}
 *   instead. A stored `update` is still shown while `error` is set, so the
 *   card degrades to the last known data rather than failing.
 * @param selection - Which trains the summary covers; 'ALL' shows the
 *   overall percentage over all trains.
 * @param error - Set while the trains stream cannot connect, e.g. when the
 *   backend is down.
 */
function TrainCard({
  update,
  selection,
  error,
}: { update: TrainsUpdate | null; selection: LineGroupSelection; error: Error | null }) {
  if (update === null && error !== null) {
    return <NoManningData />
  }
  return <TrainCardContent data={update ?? EMPTY_UPDATE} selection={selection} />
}

/**
 * Render the manning summary and progress bars for a trains update.
 *
 * @param data - The update to show; an empty one renders the loading
 *   placeholder.
 * @param selection - Which trains the summary covers.
 */
function TrainCardContent({ data, selection }: { data: TrainsUpdate; selection: LineGroupSelection }) {
  const isAll = selection === 'ALL'
  const allRoutes = [...new Set(data.trains.flatMap((train) => train.line))]
  if (allRoutes.length === 0) {
    allRoutes.push(...ALL_ROUTES)
  }
  const scopeRoutes = isAll ? allRoutes : LINE_GROUP_ROUTES[selection]
  const scopeTrains = isAll
    ? data.trains
    : data.trains.filter((train) =>
        train.line.some((line) => LINE_GROUP_ROUTES[selection].includes(line)),
      )
  const scopePct = isAll
    ? pct(data.manning_percent)
    : pct(selection === 'M1/M2' ? data.m1m2_manning_percent : data.m3m4_manning_percent)
  const scopeOk = scopePct !== null && scopePct >= MANNING_TARGET_PCT
  const scopeMannedCount = scopeTrains.filter(
    (train) => train.current_steward_ids.length > 0,
  ).length
  const scopeTrend = trendOf(scopeMannedCount, scopeTrains.length, scopePct)
  const scopeLabel = isAll ? 'alle linjer' : selection
  const barLabel = isAll ? 'Samlet bemanding' : `Bemanding ${selection}`
  const overallPct = pct(data.manning_percent)
  const mannedCount = data.trains.filter((train) => train.current_steward_ids.length > 0).length
  const overallOk = overallPct !== null && overallPct >= MANNING_TARGET_PCT
  const overallTrend = trendOf(mannedCount, data.trains.length, overallPct)

  return (
    <section className="card train-card">
      {data.trains.length === 0 ? (
        <div className="train-summary placeholder" aria-label="Ingen tog i drift">
          <div className="train-summary-main">
            <span className="placeholder-bar lines" />
            <span className="placeholder-bar count" />
          </div>
          <div className="train-summary-side">
            <span className="placeholder-bar pct" />
            <div className="train-bar slim">
              <div className="progress">
                <div className="placeholder-bar fill" />
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="train-summary">
          <div className="train-summary-main">
            <RouteBadges routes={scopeRoutes} />
            <span className="train-summary-label">Toge bemandede</span>
            <span className="train-summary-count-row">
              <span className="train-summary-count">
                {scopeMannedCount}/{scopeTrains.length}
              </span>
              {scopeMannedCount > 0 && (
                <span className="train-live">
                  <span className="train-live-dot" />
                  LIVE
                </span>
              )}
            </span>
          </div>
          <div className="train-summary-side">
            <span className="train-summary-pct-row">
              <span className="train-summary-pct">
                {scopePct === null ? '—' : `${scopePct}%`}
              </span>
              <TrendArrow trend={scopeTrend} label={`Bemandede tog i ${scopeLabel}`} />
            </span>
            <div className="train-bar slim">
              <div
                className="progress"
                role="progressbar"
                aria-valuenow={scopePct ?? 0}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={barLabel}
              >
                <div
                  className={`progress-fill${scopeOk ? '' : ' low'}`}
                  style={{ width: `${scopePct ?? 0}%` }}
                />
              </div>
              <span className="train-bar-tick" style={{ left: `${MANNING_TARGET_PCT}%` }} />
            </div>
          </div>
        </div>
      )}
      {!isAll && (
        <>
          <header className="train-card-head">
            <h2>
              <RouteBadges routes={allRoutes} />
            </h2>
            <span className="train-head-status">
              <span className="train-head-pct">
                {overallPct === null ? '—' : `${overallPct}%`}
              </span>
              <TrendArrow trend={overallTrend} label="Bemandede tog i alt" />
            </span>
          </header>
          <div className="train-bar">
            <div
              className="progress"
              role="progressbar"
              aria-valuenow={overallPct ?? 0}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Samlet bemanding"
            >
              <div
                className={`progress-fill${overallOk ? '' : ' low'}`}
                style={{ width: `${overallPct ?? 0}%` }}
              />
            </div>
            <span className="train-bar-tick" style={{ left: `${MANNING_TARGET_PCT}%` }} />
          </div>
        </>
      )}
    </section>
  )
}

export default TrainCard
