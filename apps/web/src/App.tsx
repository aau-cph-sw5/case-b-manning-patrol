/** Root component with a minimal path-based router. */
import Dashboard from './components/Dashboard'
import Home from './Home'
import Summary from './components/Summary/Summary'
import ComplianceReport from './components/ComplianceReport'

/**
 * Route to the starter, shift summary, historical compliance report or dashboard.
 *
 * There is no client-side routing: the path is read from `window.location` on
 * render, so changing page means a full page load.
 */
function App() {
  if (window.location.pathname === '/vitestarter') {
    return <Home />
  } else if (window.location.pathname === '/summary') {
    return <Summary />
  } else if (window.location.pathname === '/compliance-report') {
    return <ComplianceReport />
  }

  return <Dashboard />
}

export default App
