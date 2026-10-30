# ADR 0003. Which branching strategy should be used?

**Status.** Proposed

**Date.** 2026-09-21

**Deciders.** Sebastian Milo & Tue Elhegn, Team 3

**Related backlog items.** None

## Context

The project requires a consistent branching strategy to support parallel development while keeping stable releases separate from ongoing work. GitFlow provides a structured approach with dedicated branches for development, features, releases, and fixes. This helps avoid unclear branching and a lot of merge conflicts.

## Decision

GitFlow will be used as the branching strategy.

The `main` branch will contain stable releases, while `develop` will be used to integrate ongoing development. Supporting branches will be used for specific purposes:

* `feature/*` for new features.
* `release/*` for preparing releases.
* `hotfix/*` for urgent fixes to released versions.
* `bugfix/*` for fixes to the development version.

Features and bug fixes are merged into `develop`. Releases and hotfixes are merged into both `main` and `develop` to keep the branches synchronized.

## Consequences

### Positive impact

* Provides a clear structure for development and releases.
* Separates ongoing development from stable versions.
* Supports parallel development of features and fixes.
* Provides a clear release history through `main`.

### Potential drawbacks

* Introduces additional branches and merge operations.
* Requires consistent use of the branching conventions.
* Long-running branches may result in larger merge conflicts.
* May introduce unnecessary overhead for a small project.

## Alternatives considered

### GitHub Flow

A simpler model based on `main` and short-lived feature branches. It reduces complexity but provides less separation between development and releases.

### Trunk-based development

Changes are frequently integrated into a shared `main` branch. This reduces long-running branches but provides less isolation between ongoing development and stable releases.

## Notes

GitFlow was selected because its structured approach provides clear separation between ongoing development and stable releases while supporting parallel work within the teams.
