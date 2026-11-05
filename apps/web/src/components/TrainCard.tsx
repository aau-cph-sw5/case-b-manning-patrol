import type { TrainsUpdate } from '../api/dashboardApi'

import { BsArrowDown, BsArrowRight, BsArrowUp } from 'react-icons/bs'

import { LINE_GROUPS, LINE_GROUP_ROUTES, ROUTE_COLORS, type LineGroup } from '../utils/lineGroup.ts'

// compliance rule: a train must be manned at least 70% of running time
const MANNING_TARGET_PCT = 70

// TEMP-FAKE-DATA: hard-coded preview update (67% manned, 6/10 trains with a steward) — delete before committing
const FAKE_UPDATE: TrainsUpdate = {
  trains: Array.from({ length: 10 }, (_, i) => ({
    train_id: `fake-${i + 1}`,
    slug: `Tog ${i + 1}`,
    total_time_secs: 3600,
    manned_time_secs: i < 6 ? 3600 : 630,
    current_steward_ids: i < 6 ? ['660e8400-e29b-41d4-a716-446655440001'] : [],
    line: i < 5 ? ['M1'] : i < 6 ? ['M2'] : i < 8 ? ['M3'] : ['M4'],
  })),
  manning_percent: 0.67,
  m1m2_manning_percent: 0.67,
  m3m4_manning_percent: 0.7,
  time: '2026-11-02T10:00:00+01:00',
}

// backend ratios are 0..1; null means the group has no running time
function pct(ratio: number | null): number | null {
  return ratio === null ? null : Math.round(ratio * 100)
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

// arrow trend from the share of trains with a steward: above the 70% target is
// up (green), below is down (red), exactly at the target is flat (yellow)
function trendOf(manned: number, total: number): Trend | null {
  if (total <= 0) return null
  const ratio = manned / total
  if (ratio > MANNING_TARGET_PCT / 100) return 'up'
  if (ratio < MANNING_TARGET_PCT / 100) return 'down'
  return 'flat'
}

function TrendArrow({ trend, label }: { trend: Trend | null; label: string }) {
  if (trend === null) return null
  const Icon = trend === 'up' ? BsArrowUp : trend === 'down' ? BsArrowDown : BsArrowRight
  const cls = trend === 'up' ? 'ok-arrow' : trend === 'down' ? 'low-arrow' : 'flat-arrow'
  const text = trend === 'up' ? 'over målet' : trend === 'down' ? 'under målet' : 'på målet'
  return <Icon className={cls} aria-label={`${label} ${text}`} />
}

function TrainCard({ update, lineGroup }: { update: TrainsUpdate | null; lineGroup: LineGroup }) {
  // TEMP-FAKE-DATA: fall back to a fake update when the stream has none — delete before committing
  const data = update ?? FAKE_UPDATE
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
  const overallTrend = trendOf(mannedCount, data.trains.length)
  const groupTrend = trendOf(groupMannedCount, groupTrains.length)
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
