/**
 * Entry point: renders {@link App} into `#root` in StrictMode.
 *
 * In development StrictMode runs effects twice on mount, so the dashboard
 * stream opens, closes and opens again on load.
 */
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
