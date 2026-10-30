import Dashboard from './components/Dashboard'
import Home from './Home'

/** Render the dashboard at `/dashboard` and the Vite starter page anywhere else. */
function App() {
  if (window.location.pathname === '/dashboard') {
    return <Dashboard />
  }
  return <Home />
}

export default App
