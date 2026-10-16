# ADR 0009. An observation, which arrives after the shift it belongs to has been reported, is handled by a stated rule, rather than silently accepted

**Status:** Proposed

**Date:** 2026-10-16

**Deciders:** Sebastian Juel Milo, Héðinn Snær Arnarson, Group 3

**Related backlog items:** MET-B-006

## Context

A handheld that reconnects after a period underground will deliver observation late.
Without this rule compliance percentages are quietly wrong.


## Decision
Based on an answer from Metro in August 2026, if an observation arrives late, a report will be reissued. The report is therefore a versioned artefact rather than a file produced once. A reissue supersedes the earlier version, however the earlier version remains retrievable. 

## Consequences
Based on the work on the append-only event store (**0008-append-only-event-store-decision.md**) which stores both the handheld timestamp and the server timestamp, we already have the data required to version reports, therefore the acceptance criteria from MET-B-006: "An observation arriving out of order is placed by its observation timestamp" is trivially solved. 

Positive Impact:
- If a steward disconnects from a station, but reconnects 5 minutes after the patrol countdown will be based on when he leaves the station and not when he arrives.

Potential drawbacks: 
- Generation of the reports will be more complex, but remains a seperate issue.

## Alternatives considered
No alternatives considered as this was a requirement coming straight from Metroservice.

## Notes
This ADR only describes how the data will be stored to later generate the report and does not consider how to actually generate a report. 