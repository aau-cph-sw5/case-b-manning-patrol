import Dashboard from './components/Dashboard'
import Home from './Home'

function App() {
  if (window.location.pathname === '/dashboard') {
    return <Dashboard />
  }
  return <Home />
}

export default App
