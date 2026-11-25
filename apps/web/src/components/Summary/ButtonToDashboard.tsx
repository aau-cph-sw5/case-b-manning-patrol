import './ButtonToDashboard.css'

/**
 * Button in the topbar of the shift summary page, top right, that goes back
 * to the dashboard at `/`.
 *
 * There is no client-side routing: like the rest of the app (see App.tsx),
 * it does a full page load to the target path.
 */
export default function ButtonToDashboard() {
  return (
    <a
      className="dashboard-button"
      href="/">
      Dashboard
    </a>
  )
}
