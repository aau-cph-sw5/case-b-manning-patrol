# ADR 0008. Append-only Eventstore decision.

**Status.** Proposed 
**Date.** 2026-10-09
**Deciders.** Peter Rasmussen, Tue Elhegn, team 3
**Related backlog items.** MET-B-020

## Context

PBI MET-B-020 suggests append-only storage for the records in the database, as these are used for the compliance reports that Metro Service presents to Metro Selskabet, as evidence of manning requirements. This means we develop a database relation that has no code path for changes and only appends new events, without the possibility of updating or deleting records, in the event store. This will be treated as a source of truth for all parties.

## Decision

We will implement and enforce an append only event store with no code path updating or deleting events.

## Consequences

Positive impact
An append-only event store is a well documented concept in software engineering and is fitting for this case in particular. It is a simple solution to a critical problem.

Potential drawbacks
Having this append-only event store be source of truth and compliance-crucial, requires strict enforcement and leverage of security protocols.
This decision might complicate the development further down the line, as an append-only structure is limiting what we can do with the data in the backend.

## Alternatives considered

**Audit log versioning.** Was considered, but as the PBI already suggested append-only, it was reasonable to choose that solution.

## Notes
