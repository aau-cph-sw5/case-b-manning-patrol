/**
 * The three train manning pies on the summary page (all lines, M1/M2, M3/M4),
 * fed live by the trains SSE stream.
 */
import { useTrainStream } from '@/hooks/useTrainStream'
import { ROUTE_COLORS } from '@/utils/lineGroup'
import ManningPieChart from './ManningPieChart'

/** Render a line group name with each line in its route colour, e.g. M1/M2. */
function GroupTitle({ lines }: { lines: [string, string] }) {
  return (
    <>
      <span style={{ color: ROUTE_COLORS[lines[0]] }}>{lines[0]}</span>/
      <span style={{ color: ROUTE_COLORS[lines[1]] }}>{lines[1]}</span>
    </>
  )
}

/**
 * Render the overall pie large on the left and the two line group pies
 * stacked on the right. Shows the last saved update until the stream sends
 * one, and a notice while the connection is down.
 */
export default function TrainManningPies() {
  const { trainsUpdate, error } = useTrainStream()

  return (
    <section className="train-manning-pies">
      {error && <p className="stream-error">Forbindelsen er afbrudt, prøver igen…</p>}
      <ManningPieChart
        title="Tog bemandelse for alle linjer"
        percent={trainsUpdate?.manning_percent ?? null}
        size={300}
      />
      <div className="train-manning-pies-groups">
        <ManningPieChart
          title={<GroupTitle lines={['M1', 'M2']} />}
          percent={trainsUpdate?.m1m2_manning_percent ?? null}
          size={160}
        />
        <ManningPieChart
          title={<GroupTitle lines={['M3', 'M4']} />}
          percent={trainsUpdate?.m3m4_manning_percent ?? null}
          size={160}
        />
      </div>
    </section>
  )
}
