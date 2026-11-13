/** Root component with a minimal path-based router. */
import Dashboard from './components/Dashboard'
import Home from './Home'

/**
 * Render the Vite starter at `/vitestarter` and the dashboard page at any other
 * path.
 *
 * There is no client-side routing: the path is read from `window.location` on
 * render, so changing page means a full page load.
 */
function App() {
  if (window.location.pathname === '/vitestarter') {
    return <Home />
  }
  
  return <Dashboard />
}

export default App
