/** Root component with a minimal path-based router. */
import Dashboard from './components/Dashboard'
import Home from './Home'

/**
 * Render the dashboard at `/dashboard` and the Vite starter page at any other
 * path.
 *
 * There is no client-side routing: the path is read from `window.location` on
 * render, so changing page means a full page load.
 */
function App() {
  if (window.location.pathname === '/dashboard') {
    return <Dashboard />
  }
  return <Home />
}

export default App
