/**
 * The at-risk threshold in minutes, held in module state for the page.
 *
 * Not persisted: every page load starts at 10 until the dashboard has fetched
 * the backend's value.
 */

/**
 * At-risk threshold in minutes. Exported as a live binding, so importers see
 * the latest value passed to {@link setRiskTime}.
 */
let RiskTime: number = 10;

/** Return the current at-risk threshold in minutes. */
function getRiskTime(): number {
  return RiskTime;
}

/** Set the at-risk threshold in minutes. Notifies no one and does not call the backend. */
function setRiskTime(value: number): void {
  RiskTime = value;
}

export { RiskTime, getRiskTime, setRiskTime };
