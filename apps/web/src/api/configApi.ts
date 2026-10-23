const URL = '/api/v2/config/at-risk-threshold'

export async function getAtRiskThreshold(): Promise<number> {
  const res = await fetch(URL)
  if (!res.ok) throw new Error(`GET failed: ${res.status}`)
  return (await res.json()).at_risk_threshold_minutes
}

export async function setAtRiskThreshold(minutes: number): Promise<void> {
  const res = await fetch(URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ at_risk_threshold_minutes: minutes }),
  })
  if (!res.ok) throw new Error(`POST failed: ${res.status}`)
}