# Station dataset

`stations.v1.json` is the data source for the station network: which lines
exist, which stations exist, and which patrol areas (concourse and platform)
each station has. It is loaded into the database by `load_stations` in
`src/db/ingest.py`, which runs every time the app starts; the code contains no
hardcoded stations.

## What the file contains

| Level | Field | Meaning |
|---|---|---|
| Top | `version` | Audit stamp of the dataset contents; not the meaning of "versioned" (see below). |
| Top | `lines` | The lines in scope, each with an `id` and `name`. |
| Top | `stations` | One entry per station. |
| Station | `id` | Stable identifier of the station (`STN-001` … `STN-042`). |
| Station | `name` | Human-readable name. |
| Station | `line_ids` | The lines serving this station. A station serving two lines appears **once** here with two entries. |
| Station | `patrol_areas` | The distinct patrol areas of this station. |
| Area | `id` | Stable identifier of the area (`PA-001-P`). Survives a beacon swap. |
| Area | `kind` | `platform` or `concourse`. |
| Area | `beacon_id` | The identifier of the beacon that **names** this area. An attribute, not the identity: if the physical beacon is replaced, only this value changes. |

Every station has exactly one `platform` area and zero or one `concourse`
area. A station can therefore have either a platform only, or both.

Concourse and platform are separate entries in `patrol_areas`, not flags on
the station, so coverage can be computed per level independently (source
story B2.1).

## Dataset statistics

| Group | Stations | Concourses |
|---|---|---|
| M1 / M2 | 20 (STN-001 … STN-020) | 5 (STN-001, 005, 011, 015, 020) |
| M3 / M4 | 22 (STN-021 … STN-042) | 20 (all except STN-022, 027) |
| **Total** | **42** | **25** |

Patrol areas in total: 42 platforms + 25 concourses = **67**.

Interchanges (serving two lines): STN-010, STN-011 (M1+M2) and
STN-031, STN-032 (M3+M4).

## Beacon ID scheme

Beacon IDs share the base `660e8400-e29b-41d4-a716-44665544`; the last hex
group encodes the area:

| Suffix | Area |
|---|---|
| `0001`–`002a` | Platform of station 1–42 |
| `0081`–`00aa` | Concourse of station 1–42 (station number + `0x80`) |
| `0101`–`0122` | Trains `train-1` … `train-34` (M1 / M2, `trains.v1.json`, see below) |
| `0201`–`0227` | Trains `train-35` … `train-73` (M3 / M4, `trains.v1.json`, see below) |

## How the file satisfies the acceptance criteria

| Criterion | How |
|---|---|
| Each station maps to its identifier, its line, and its distinct patrol areas | Every station entry carries `id`, `line_ids`, and a `patrol_areas` list with one entry per area. |
| Each patrol area carries the identifier of the beacon that names it | Every area entry has a `beacon_id` field. |
| The dataset is loaded from a versioned file and reloading is idempotent | The network lives in this JSON file under version control, not in code. `load_stations` reads the file and replaces the contents of the `station` and `patrolarea` tables in one transaction, so reloading it any number of times yields identical database state. `tests/test_ingest.py` loads the file twice and checks for 42 stations and 67 patrol areas both times, with foreign keys enforced. Because the tables are replaced on every start, rows added to them by hand are lost. |
| Stations serving two lines are modelled once and referenced twice rather than duplicated | STN-010, STN-011, STN-031, STN-032 appear once, with both lines in `line_ids`. In the database they are one `station` row whose `line_ids` column holds both lines. |
| A station added to the file appears in the system without a code change | Add an entry to `stations` and restart the app; `load_stations` reads the file, so no schema or code change is needed. |

# Train dataset

`trains.v1.json` lists the fleet. `load_trains` (`src/db/ingest.py`) loads it
into the `train` and `trainline` tables on every start. The app calls
`load_reference_data`, which runs `load_stations` first, because every
`line_ids` value must exist in `stations.v1.json` and reloading the stations
clears the train-line links. Do not call `load_stations` on its own, or every
train loses its lines.

| Field | Meaning |
|---|---|
| `train_id` | Stable train identifier. Survives a beacon swap. |
| `slug` | Human-readable name shown on the dashboard. |
| `beacon_id` | The beacon that names the train. An attribute, not the identity. |
| `line_ids` | The lines the train can run on. Trains are shared within M1/M2 and within M3/M4, so every train lists both lines of its group. |

| Group | Trains | Slugs | ID / beacon suffix |
|---|---|---|---|
| M1 / M2 | 34 | `train-1` … `train-34` | `0101` … `0122` |
| M3 / M4 | 39 | `train-35` … `train-73` | `0201` … `0227` |

Beacons use the station base `660e8400-e29b-41d4-a716-44665544` and IDs the
base `770e8400-e29b-41d4-a716-44665544`, with the same suffix. The fleet size
is an estimate, not a Metro figure. Every train counts toward the manned-time
denominator for the whole shift; whether a train is "in service" is left to a
separate ADR.

# Shift schedule

`shifts.v1.json` defines when the night shift runs. Coverage is computed per
shift: `CoverageUpdater` reads the file once at startup through
`ShiftSchedule.from_file` (`src/services/shared/shift_schedule.py`).

| Field | Meaning |
|---|---|
| `version` | Audit stamp of the file contents. |
| `timezone` | IANA time zone the shift times are in (`Europe/Copenhagen`), so daylight saving is handled. |
| `night_shift.start` | Local time the shift starts every night (`00:00`). This is `shift_start_time`. |
| `night_shift.end` | Local time the shift ends (`06:00`). An end before the start means the shift crosses midnight, e.g. `22:00`–`06:00`. |

`shift_start_time` is the scheduled start of the shift, not a patrol-session
START event: a steward can send START several times per shift, for example
after a break.

How the schedule is used:

- **Coverage resets every shift.** Only the part of each visit inside the
  current shift counts; visits from an earlier shift are ignored.
- **Every area starts covered.** The shift start counts as covered for one
  window (60 min), so an area never patrolled becomes overdue one window
  after the shift starts, and that episode reaches the overdue log.
- **Between shifts the last shift is frozen.** Outside shift hours coverage is
  evaluated at the end of the last shift, so nothing new becomes overdue during
  the day.

Changing the shift times only needs an edit to this file and a restart.

# Permission matrix

`permissions.v1.json` defines the role-based access policy based on Metro's
decision of 7 November 2026 (source story B6.2), with the team's proposed
interpretations in [ADR 0013](../../../../docs/docs/adr/0013-presence-and-shared-coverage-access.md).
The ADR remains Proposed pending team review. The matrix is policy data;
runtime loading and enforcement have not yet been implemented.

Individual presence records and shared station patrol coverage are separate
data categories. A shared countdown may reflect another steward's patrol
without granting access to that steward's identity or individual records.
Only the Operations Administrator may read historical individual presence
records; roles scoped to `current` cannot reach past shifts.

| Level | Field | Meaning |
|---|---|---|
| Top | `version` | Revision stamp of the policy contents; `2026-11-10.1` includes the ADR 0013 proposal. |
| Top | `source` | Provenance of the matrix. |
| Top | `default` | `deny`: anything not granted to a role is denied. This is what gives the IT Administrator no presence access. |
| Top | `audit.log_every_individual_presence_access` | Every read of an individual steward record must be written to the B-020 audit record. |
| Role | `role` / `label` | Stable role identifier / human-readable name. |
| Grant | `data` | `presence` = individual steward presence records; `coverage` = shared station patrol status and countdowns without individual records or identities; `reference` = the registration sheet (locations, trains, beacons). |
| Grant | `subject` | For `presence`, `own` = only the role holder's records and `all` = every steward's records. For `coverage`, `all` permits the shared result calculated from all contributing stewards; it does not permit access to their records. For `reference`, `all` covers all reference entities within the grant's line scope. |
| Grant | `lines` | `own` = the caller's assigned M1/M2 or M3/M4 line group, resolved from trusted identity data; `all` = all lines. Supervisor presence scope and steward coverage scope are team decisions, not explicit Metro restrictions. |
| Grant | `shift_scope` | `current` = only the current shift (see `shifts.v1.json`; the exact current/history boundary is an ADR topic); `all` = current and historical shifts. Carries no time restriction for `reference` data. |

The five roles, as granted:

| Role | Presence data | Shared coverage | Reference data |
|---|---|---|---|
| Steward | Own records, all lines, current shift | Assigned line group, current shift | — |
| Steward Supervisor | All records, assigned line group, current shift | Assigned line group, current shift | — |
| Control Room Operator | All records, all lines, current shift | All lines, current shift | — |
| Operations Administrator | All records, all lines, current and historical | All lines, current shift | — |
| IT Administrator | — | — | All (registration and replacement of locations, trains, beacons) |

Stewards' own current-shift presence records are not restricted by line.
Supervisor presence access is restricted to their assigned line group.
The team decision of 10 November 2026 resolves the steward coverage scope
left open by ADR 0013: shared patrol status and countdowns are restricted to
the steward's assigned line group.

The backend must calculate shared coverage and send only the permitted
result. Hiding individual records in the Android interface after receiving
them does not enforce the policy. A train stream containing steward IDs is
individual presence disclosure and requires a matching `presence` grant;
a `coverage` grant alone does not authorize it. Apply the same distinction
to initial responses, stream updates and reconnects.

Individual presence disclosures must be audited through B-020. Shared
coverage alone does not trigger that individual-record audit requirement;
additional coverage logging is a separate policy decision. A countdown
change can still reveal that a patrol occurred and may allow someone with
outside knowledge to infer who performed it.

Presence and coverage grants describe read access, not permission to correct
records. The existing reference-data grant describes the IT Administrator's
registration and replacement responsibilities; action-specific enforcement
remains to be defined. The exact current/history boundary needs a separate
ADR, and these coverage grants do not authorize historical coverage reports.
