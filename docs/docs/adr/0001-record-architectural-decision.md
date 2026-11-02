# ADR 0001. Should architectural decisions be documented using ADRs?

**Status.** Proposed

**Date.** 2026-09-18

**Deciders.** Marcus Eckstrøm, Peter Rasmussen & Tue Elhegn, Team 3

**Related backlog items.** None

## Context

During the development of the system, key architectural decisions will be made that affect the design, implementation, and development of the project. These decisions often involve choosing between multiple alternatives based on requirements, constraints, and trade-offs.

Without a structured way of documenting these decisions, the reasoning behind them may be lost over time. This can make it difficult for team members and stakeholders to understand why a particular solution was chosen and which alternatives were considered.

Architectural Decision Records (ADRs) provide a consistent method for documenting architectural decisions and keeping track of the iterations of those.

## Decision

Architectural Decision Records will be used throughout the project to document significant architectural decisions.

Each ADR will describe the context of the decision, the chosen solution, its consequences, and relevant alternatives that were considered. ADRs will be numbered sequentially and stored alongside the project documentation, allowing architectural decisions and their reasoning to be traced throughout the development process.

An ADR cannot be changed, so if a decision is changed, a new version will be made with links to the superseded ADR.

## Consequences

### Positive impact

* Provides a consistent structure for documenting architectural decisions.
* Preserves the reasoning behind decisions and the alternatives that were considered.
* Makes architectural decisions easier for team members and stakeholders to understand and review.
* Provides a historical record that can support future changes to the system.

### Potential drawbacks

* Writing and maintaining ADRs requires additional development and documentation time.
* ADRs can become outdated if architectural changes are made without updating or superseding the relevant records.
* Determining which decisions are significant enough to require an ADR requires judgement from the development team.

## Alternatives considered

### No formal decision documentation

Architectural decisions could be discussed within the team and implemented without being formally recorded. This requires less documentation but makes it difficult to understand the reasoning behind previous decisions later in the project.

### General project documentation

Architectural decisions could be documented as part of the general project documentation. This keeps documentation centralized but makes individual decisions and their consequences harder to identify and trace.

### Comments in source code

Architectural reasoning could be documented close to the implementation through comments. This provides context directly within the code but is unsuitable for decisions that affect multiple components or concern the overall architecture.

## Notes

This ADR establishes the use of ADRs as the project's method for documenting architectural decisions. As the first ADR, it also defines the general structure that subsequent ADRs should follow. Future ADRs should use the same sections and numbering scheme to maintain consistency across the project.
