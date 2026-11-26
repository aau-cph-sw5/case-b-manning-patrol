/**
 * Pie chart of how much of the running time trains were manned, with a dashed
 * marker at the 70% compliance target.
 */
import { PieChart } from '@mui/x-charts/PieChart'
import { useDrawingArea } from '@mui/x-charts/hooks'
import './ManningPieChart.css'

/** Compliance rule: a train must be manned at least 70% of its running time. */
export const MANNING_TARGET_PCT = 70

const MANNED_COLOR = '#8fdca8'
const UNMANNED_COLOR = '#f5a3a3'
const NO_DATA_COLOR = '#d9d9d9'

/**
 * Dashed radius from the centre to where 70% falls on the circle.
 *
 * The pie starts at 12 o'clock and runs clockwise, so the manned slice ends
 * past this line exactly when the target is met.
 */
function TargetMarker() {
  const { left, top, width, height } = useDrawingArea()
  const cx = left + width / 2
  const cy = top + height / 2
  const r = Math.min(width, height) / 2
  const angle = (MANNING_TARGET_PCT / 100) * 2 * Math.PI
  return (
    <line
      x1={cx}
      y1={cy}
      x2={cx + r * Math.sin(angle)}
      y2={cy - r * Math.cos(angle)}
      stroke="#333"
      strokeWidth={1.5}
      strokeDasharray="6 4"
    />
  )
}

/**
 * Render one manning pie with a title and a pass/fail line under it.
 *
 * @param percent - Manning percentage 0..100 from the trains stream; null
 *   when the group has no running time, which renders a grey "no data" pie.
 * @param size - Width and height in pixels.
 */
export default function ManningPieChart({
  title,
  percent,
  size,
}: {
  title: React.ReactNode
  percent: number | null
  size: number
}) {
  const hasData = percent !== null
  const manned = hasData ? Math.min(Math.max(percent, 0), 100) : 0
  const ok = hasData && manned >= MANNING_TARGET_PCT

  const data = hasData
    ? [
        { id: 'manned', value: manned, label: 'Bemandet', color: MANNED_COLOR },
        { id: 'unmanned', value: 100 - manned, label: 'Ubemandet', color: UNMANNED_COLOR },
      ]
    : [{ id: 'none', value: 100, label: 'Ingen data', color: NO_DATA_COLOR }]

  return (
    <figure className="manning-pie">
      <figcaption className="manning-pie-title">{title}</figcaption>
      <PieChart
        width={size}
        height={size}
        hideLegend
        margin={{ top: 4, right: 4, bottom: 4, left: 4 }}
        series={[
          {
            data,
            startAngle: 0,
            endAngle: 360,
            valueFormatter: (item) => `${item.value.toFixed(1)}%`,
          },
        ]}
      >
        <TargetMarker />
      </PieChart>
      <p className={`manning-pie-status ${hasData ? (ok ? 'ok' : 'low') : ''}`}>
        {hasData
          ? `${Math.round(manned)}% bemandet · ${ok ? 'mål på 70% opnået' : 'under målet på 70%'}`
          : 'Ingen køretid endnu'}
      </p>
    </figure>
  )
}
