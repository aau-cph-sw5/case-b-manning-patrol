# Station dataset

`stations.v1.json` is the data source for the station network: which lines
exist, which stations exist, and which patrol areas (concourse and platform)
each station has. It is loaded into the database by the ingest step; the code
contains no hardcoded stations.

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
| `0050`, `0060` | Trains (not part of this file, see `fixtures/`) |

## How the file satisfies the acceptance criteria

| Criterion | How |
|---|---|
| Each station maps to its identifier, its line, and its distinct patrol areas | Every station entry carries `id`, `line_ids`, and a `patrol_areas` list with one entry per area. |
| Each patrol area carries the identifier of the beacon that names it | Every area entry has a `beacon_id` field. |
| The dataset is loaded from a versioned file and reloading is idempotent | The network lives in this JSON file under version control, not in code. The ingest step reads the file and replaces the DB contents in one transaction, so reloading it any number of times yields identical database state. |
| Stations serving two lines are modelled once and referenced twice rather than duplicated | STN-010, STN-011, STN-031, STN-032 appear once, with both lines in `line_ids`. In the database they are one `station` row with two `station_line` rows. |
| A station added to the file appears in the system without a code change | Add an entry to `stations` and reload; the ingest reads the file, so no schema or code change is needed. |
