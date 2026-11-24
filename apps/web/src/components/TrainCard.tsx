/**
 * Dashboard card showing train manning from the trains SSE stream: the share
 * of running time trains were manned, overall and for the selected line group,
 * against the 70% compliance target.
 */

import type { TrainsUpdate } from '../api/dashboardApi'

import { LINE_GROUPS, LINE_GROUP_ROUTES, type LineGroup } from '../utils/lineGroup.ts'
import { trendOf } from '../utils/trainManning.ts'
import { NoManningData, RouteBadges, TrendArrow } from './TrainCardParts.tsx'

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

/**
 * Render manning for all trains and for the trains serving `lineGroup`.
 *
 * @param update - Latest trains stream event; null before the first one. Null
 *   without an error renders the loading placeholder, the same as a stream
 *   with no trains; null together with `error` renders {@link NoManningData}
 *   instead. A stored `update` is still shown while `error` is set, so the
 *   card degrades to the last known data rather than failing.
 * @param error - Set while the trains stream cannot connect, e.g. when the
 *   backend is down.
 */
function TrainCard({ update, lineGroup, error }: { update: TrainsUpdate | null; lineGroup: LineGroup; error: Error | null }) {
  if (update === null && error !== null) {
    return <NoManningData />
  }
  return <TrainCardContent data={update ?? EMPTY_UPDATE} lineGroup={lineGroup} />
}

/**
 * Render the manning summary and progress bars for a trains update.
 *
 * @param data - The update to show; an empty one renders the loading
 *   placeholder.
 * @param lineGroup - Line group whose trains the summary counts.
 */
function TrainCardContent({ data, lineGroup }: { data: TrainsUpdate; lineGroup: LineGroup }) {
  const groupRoutes = LINE_GROUP_ROUTES[lineGroup]
  const groupPct = pct(
    lineGroup === 'M1/M2' ? data.m1m2_manning_percent : data.m3m4_manning_percent,
  )
  const overallPct = pct(data.manning_percent)
  const groupOk = groupPct !== null && groupPct >= MANNING_TARGET_PCT
  const overallOk = overallPct !== null && overallPct >= MANNING_TARGET_PCT
  const groupTrains = data.trains.filter((train) =>
    train.line.some((line) => LINE_GROUP_ROUTES[lineGroup].includes(line)),
  )
  const mannedCount = data.trains.filter((train) => train.current_steward_ids.length > 0).length
  const groupMannedCount = groupTrains.filter(
    (train) => train.current_steward_ids.length > 0,
  ).length
  const overallTrend = trendOf(mannedCount, data.trains.length, overallPct)
  const groupTrend = trendOf(groupMannedCount, groupTrains.length, groupPct)
  const allRoutes = [...new Set(data.trains.flatMap((train) => train.line))]
  if (allRoutes.length === 0) {
    allRoutes.push(...LINE_GROUPS.flatMap((group) => LINE_GROUP_ROUTES[group]))
  }

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
            <RouteBadges routes={groupRoutes} />
            <span className="train-summary-label">Toge bemandede</span>
            <span className="train-summary-count-row">
              <span className="train-summary-count">
                {groupMannedCount}/{groupTrains.length}
              </span>
              {groupMannedCount > 0 && (
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
                {groupPct === null ? '—' : `${groupPct}%`}
              </span>
              <TrendArrow trend={groupTrend} label={`Bemandede tog i ${lineGroup}`} />
            </span>
            <div className="train-bar slim">
              <div
                className="progress"
                role="progressbar"
                aria-valuenow={groupPct ?? 0}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={`Bemanding ${lineGroup}`}
              >
                <div
                  className={`progress-fill${groupOk ? '' : ' low'}`}
                  style={{ width: `${groupPct ?? 0}%` }}
                />
              </div>
              <span className="train-bar-tick" style={{ left: `${MANNING_TARGET_PCT}%` }} />
            </div>
          </div>
        </div>
      )}
      <header className="train-card-head">
        <h2>
          <RouteBadges routes={allRoutes} />
        </h2>
        <span className="train-head-status">
          <span className="train-head-pct">{overallPct === null ? '—' : `${overallPct}%`}</span>
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
    </section>
  )
}

export default TrainCard
