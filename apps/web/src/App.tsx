/** Root component with a minimal path-based router. */
import Dashboard from './components/Dashboard'
import Home from './Home'
import Summary from './components/Summary'

/**
 * Render the Vite starter at `/vitestarter`, the shift summary page at
 * `/summary` and the dashboard page at any other path.
 *
 * There is no client-side routing: the path is read from `window.location` on
 * render, so changing page means a full page load.
 */
function App() {
  if (window.location.pathname === '/vitestarter') {
    return <Home />
  } else if (window.location.pathname === '/summary') {
    return <Summary />
  }

  return <Dashboard />
}

export default App
