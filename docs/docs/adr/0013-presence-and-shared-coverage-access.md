# ADR 0013. Separate individual presence access from shared patrol coverage.

**Status.** Proposed

**Date.** 2026-11-10

**Deciders.** Pending team review

**Related backlog items.** MET-B-023, MET-B-020, MET-B-022

## Context

[MET-B-023](https://github.com/aau-cph-sw5/case-b-manning-patrol/issues/21) limits a steward to their own presence records for the current shift. Steward Supervisors and Control Room Operators may access other stewards' current-shift records, while only the Operations Administrator may access historical presence records. The IT Administrator's reference-data responsibilities do not imply presence access.

The Android steward app also shows shared station patrol status and countdowns. A patrol performed by one steward updates the coverage information used by the others, helping them decide where another patrol is needed. The current station stream carries area coverage information without steward identities; the separate train stream includes individual steward IDs, as described in [ADR 0012](0012-train-manning-stream.md).

The permission matrix currently describes individual presence and reference data, but has no explicit category for shared patrol coverage. Its default-deny rule therefore needs an explicit coverage grant if stewards are to keep using the shared countdowns.

The PBI explicitly gives Control Room Operators access across all lines. It does not explicitly limit supervisors to particular lines. The team's operational interpretation is that a supervisor works within either the M1/M2 or M3/M4 line group, and their access should follow that assignment. This restriction is a team proposal, not an explicit Metro requirement.

## Decision

### Individual presence and shared coverage

Treat individual steward presence and shared station patrol coverage as separate data categories.

- Individual presence includes steward identities, device identifiers linked to stewards, and individual patrol or connection records. Stewards may read only their own records from the current shift.
- Shared patrol coverage includes a station area's current patrol status and countdown until another patrol is needed. Stewards may read this information even when another steward's activity contributed to it.

The permission matrix must grant shared coverage access explicitly. Permission to read coverage does not grant permission to read the individual records used to calculate it. This decision grants access to current operational coverage; it does not grant access to historical coverage reports or change the underlying coverage calculation.

### Backend disclosure boundary

Calculate shared coverage on the backend and send only the permitted coverage result. A steward's shared coverage response must not include other stewards' identities, device IDs, individual events, or links that expose those records. Sending individual records to a phone and hiding them in the interface does not enforce this boundary.

Classify responses by their contents. A train stream containing individual steward IDs discloses individual presence and cannot be authorized using a shared coverage grant alone. Apply the same distinction to initial responses, subsequent stream updates, and reconnects.

### Supervisor line scope

Restrict a Steward Supervisor's individual presence access to the current shift and their assigned M1/M2 or M3/M4 line group. Resolve the assignment from trusted caller identity data. Control Room Operators retain current-shift access across all lines; Operations Administrators retain current and historical presence access across all lines.

The assignment is a line group, rather than necessarily a single line. The matrix's current `lines: own` wording must be clarified before enforcement is implemented. This ADR does not decide the geographic scope of stewards' shared coverage access.

### Auditing and remaining policy decisions

Disclosures of individual steward records remain subject to the MET-B-020 access-audit requirement. Reading shared coverage alone does not constitute disclosure of an individual steward record under this distinction. Any additional logging of coverage access is a separate policy decision.

This ADR does not grant correction or registration permissions. It also leaves the exact current-to-historical shift boundary to a separate ADR.

## Consequences

Positive impact

- Stewards can coordinate patrols through shared countdowns while their access to individual records remains restricted.
- Backend authorization can distinguish coverage responses from responses that disclose individual presence.
- Supervisor access follows the team's stated line-group responsibilities without expanding it to the whole network.

Potential drawbacks

- A countdown change can reveal that a patrol occurred. In a quiet station, someone with outside knowledge may infer who performed it. Shared coverage is therefore not a guarantee of anonymity.
- Adding an identity or individual event field to a coverage response changes its access implications and requires a policy review.
- Line-group assignments and stations served by multiple lines need consistent enforcement rules and tests.

## Alternatives considered

**Restrict countdowns to the caller's own patrols.** This would hide patrols performed by colleagues and could send stewards to areas that are already covered.

**Allow every steward to read all current-shift individual records.** This would support coordination but exceed the PBI's own-record restriction.

**Filter individual records only in the Android interface.** This would still disclose the records through the API and would allow callers to bypass the interface.