/**
 * At-risk threshold in minutes, shared in memory by the dashboard.
 *
 * Starts at 10 and is not persisted; the backend's value replaces it once
 * the dashboard has fetched it. Importers get a live binding, so they see
 * changes made through {@link setRiskTime}.
 */
let RiskTime: number = 10;

/** Return the current at-risk threshold in minutes. */
function getRiskTime(): number {
  return RiskTime;
}

/**
 * Set the at-risk threshold in minutes.
 *
 * Only updates this module; it does not re-render anything or reach the
 * backend.
 */
function setRiskTime(value: number): void {
  RiskTime = value;
}

export { RiskTime, getRiskTime, setRiskTime };
