import './ButtonToSummary.css'

/**
 * Button in the topbar, right next to the line-group switch, that opens the
 * shift summary page at `/summary`.
 *
 * There is no client-side routing: like the rest of the app (see App.tsx),
 * it does a full page load to the target path.
 */
export default function ButtonToSummary() {
  return (
    <a
      className="summary-button"
      href="/summary">
      Opsummering
    </a>
  )
}
