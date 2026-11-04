# ADR 0010. Patrol completion: rolling hour and independent levels.

**Status.** Proposed
**Date.** 2026-10-16
**Deciders.** Asbjørn Gosvig, Jakob Michaelsen, Marcus Linde, Nichlas Christiansen, Rohan Atik, Ryan Zachariasen, team 8
**Related backlog items.** MET-B-007, MET-B-008, MET-B-009, MET-B-012, MET-B-013, MET-B-014, MET-B-015, MET-B-024

## Context

The requirement states that every station level is patrolled hourly. When determining how to track when an area was last manned there are different ways of implementing it, and two questions must be answered:

1. **What does "hourly" mean?** A level could be checked against fixed wall-clock hours (e.g. 14:00–14:59, a patrol per bucket), or against a rolling 60-minute window: a level is compliant at a given moment if there is evidence of coverage at some point in the last hour.
2. **Are the levels independent?** A station's levels (concourse and platform) are physically very close to each other, often only a staircase apart, and a steward visiting one will usually visit the other soon after. There is therefore also the question of their independence: should a visit to one level count for the station as a whole, or must each level show coverage on its own?

The acceptance criteria of the related backlog items already speak of each level separately, which points towards independent evaluation.

## Decision

We use a rolling hour for determining whether something is manned or not: a level is compliant at time *t* if patrol role is fuldfilled for that level within the last 60 minutes.

The two levels are computed independently.

## Consequences

Positive impact

- Faithful to the plain reading of "patrolled hourly": at any moment, the last hour must contain a patrol. There is no way for two patrols almost two hours apart to both count.
- Simple to compute. Compliance at time *t* is a lookup for records in [*t* − 60 min, *t*]. No mutable "patrol completed" state has to be maintained; the append-only event store remains the single source of truth and compliance is derived from it.
- Independence matches the acceptance criteria and prevents one level from masking a gap on the other.

Potential drawbacks

- Compliance decays with time, not only with events: a level can go from compliant to non-compliant without any new record arriving, as an older patrol slides out of the window. Dashboards and alerts must therefore re-evaluate on a timer, not only on ingestion.

- Any single observation counts as coverage. It documents presence within the hour, not that a full patrol was performed — a limitation inherited from beacon-based presence assertion (ADR 0002).

- Independent levels add patrol work: a steward assigned to train manning may often cover the platform frequently, and in many cases then have to also return to the concourse solely to satisfy its patrol requirement.   
 
## Alternatives considered

**Fixed wall-clock hours.** Treat each [hh:00, hh:59] bucket as an hour and require a patrol in every bucket. Rejected: patrols at 14:01 and 15:59 leave a gap of almost two hours yet both buckets pass, which contradicts the intent of hourly patrolling. The rolling window is the stricter reading.

**One area per station.** Treat the concourse and platform as a single area so that a visit to either covers the station. Rejected: the requirement applies to every level, and a steward can serve the platform without ever reaching the concourse. The acceptance criteria already treat the levels separately.

**Completion-based cadence.** Declare a patrol complete when the steward leaves the level (after the tolerated gap, ADR 0006) and require the next patrol within 60 minutes of that completion. Rejected: it depends on reliably detecting an exit, which is weaker than detecting presence, and it requires mutable per-level state that the append-only event store deliberately does not provide.

## Notes


