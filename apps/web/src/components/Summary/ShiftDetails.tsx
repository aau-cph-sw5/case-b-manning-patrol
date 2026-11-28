import './ShiftDetails.css'

type ShiftDetailsProps = {
  shiftDate: string
  startedAt: string
  finishedAt: string
  reportGeneratedAt: string
}

export default function ShiftDetails({
  shiftDate,
  startedAt,
  finishedAt,
  reportGeneratedAt,
}: ShiftDetailsProps) {
  return (
    <section className="shift-details">
      <dl>
        <div>
          <dt>Vagtdato</dt>
          <dd>{shiftDate}</dd>
        </div>
        <div>
          <dt>Vagt startet</dt>
          <dd>{startedAt}</dd>
        </div>
        <div>
          <dt>Vagt afsluttet</dt>
          <dd>{finishedAt}</dd>
        </div>
        <div>
          <dt>Rapport genereret</dt>
          <dd>{reportGeneratedAt}</dd>
        </div>
      </dl>
    </section>
  )
}