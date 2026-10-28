# ADR 0007. PostgreSQL as database

**Status.** Proposed

**Date.** 2026-10-07

**Deciders.** Peter Rasmussen, Tue Elhegn, Maya Lauritsen, Markus Jørgensen, Jacob Jensen, Signe Jensen, Patrick Hallberg, Victor Zacho, team 3, team 2

**Related backlog items.** MET-B-004, MET-B-013, MET-B-018, MET-B-019, MET-B-020, MET-B-021, MET-B-023, MET-B-024

## Context

The project uses relational data, including reference data such as stations and patrol areas, alongside dynamic data in the form of steward connection and disconnection events. The reference data is used to associate events with locations in the metro network. PostgreSQL supports these relational relationships while also providing JSON and JSONB column types, allowing event payloads to be stored as flexible documents within a relational database.

The database systems course teaches PostgreSQL, giving the team existing experience with the technology. PostgreSQL also satisfies the database requirements identified by the project. Other database systems, including more specialized solutions such as EventStoreDB, were considered, but their additional technological overhead was deemed unnecessary.

This ADR is related to PBI MET-B-020, which does not explicitly require implementation yet. However, the teams prioritized making the database decision now, as Sprint 2 is focused on designing the database.

## Decision

PostgreSQL is selected as the database for the backend.

## Consequences

The decision provides developers with a defined database technology and a concrete platform to build and test against. It also allows testing to progress from unit testing towards integration testing against the selected database.

Choosing PostgreSQL introduces further technical decisions regarding database drivers, ORMs, deployment, and containerization. These decisions will need to be addressed as development progresses.

The choice also means that the project's append-only event requirements will be handled within PostgreSQL rather than through a specialized event-store database.

## Alternatives considered

**EventStoreDB.** A specialized database system that is well suited to the append-only event requirement. However, it was considered excessive for the project's needs, given the additional technological overhead it would introduce.

**Other SQL databases.** Other relational database systems could satisfy the project's requirements. No project-specific reason strongly favored one over another. PostgreSQL was the natural choice given the team's existing experience with it through the database systems course.

## Notes
