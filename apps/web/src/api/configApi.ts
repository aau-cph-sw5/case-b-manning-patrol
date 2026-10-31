const URL = '/api/v2/config/at-risk-threshold'

/*At-risk threshold configuration as defined in the contract.*/
export interface AtRiskThreshold {
  at_risk_threshold_minutes: number
}

/*Parses the contract's Error schema ({ code, message }) on failure*/
async function toError(res: Response): Promise<Error> {
  try {
    const body = await res.json()
    return new Error(body.message ?? `Request failed: ${res.status}`)
  } catch {
    return new Error(`Request failed: ${res.status}`)
  }
}

export async function getAtRiskThreshold(): Promise<AtRiskThreshold> {
  const res = await fetch(URL)
  if (!res.ok) throw await toError(res)
  return (await res.json()) as AtRiskThreshold
}

export async function setAtRiskThreshold(minutes: number): Promise<AtRiskThreshold> {
  const res = await fetch(URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ at_risk_threshold_minutes: minutes }),
  })
  if (!res.ok) throw await toError(res)
  return (await res.json()) as AtRiskThreshold
}