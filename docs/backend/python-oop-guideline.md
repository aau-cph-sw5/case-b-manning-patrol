# Backend design guideline (Python)

**Status:** Draft, proposed for team agreement
**Applies to:** `services/api`
**Last updated:** 2026-11-03

This guideline describes how we structure backend code: when to write a
class, which layer a piece of code belongs in, and the conventions every
layer shares. It follows Python's own conventions, not Java or C#. In Python
a class is one tool next to modules and functions, and a module of functions
is often the more Pythonic choice.

The goal is predictability: a developer from another group should be able to
guess where a piece of logic lives and what shape it has before opening the
file. It is a guide, not a rulebook for every case. When a case is not
covered, follow the closest rule and its "Why", and raise it in review.

Docstring and formatting rules are in [AGENTS.md](../../AGENTS.md) and are
not repeated here.

## How to use this guideline

- Read sections 1 and 2 once. They answer most "where does this go?"
  questions.
- Part A (`OOP-n`) covers classes and patterns. Part B (`BE-n`) covers
  conventions every layer shares: wiring, transactions, time, async and
  errors.
- Use the checklist in section 5 in pull request reviews. Rules are numbered
  so a review comment can point to one.
- While the status is Draft, follow the guideline for new code. Section 7
  lists the choices that may still change.

**Adoption.** Apply the guideline to new code and to code your backlog item
already changes. Do not convert unrelated code while you are there
(AGENTS.md rule 3). Existing code is converted by dedicated refactoring
items.

## Contents

1. [When to write a class](#1-when-to-write-a-class)
2. [Layers: where code goes](#2-layers-where-code-goes)
3. [Terms](#3-terms)
4. [Rules](#4-rules)
   - Part A, classes and patterns: OOP-1 to OOP-6
   - Part B, backend conventions: BE-1 to BE-5
5. [Review checklist](#5-review-checklist)
6. [Tooling](#6-tooling)
7. [Open decisions](#7-open-decisions)
8. [Sources](#8-sources)

## 1. When to write a class

Pick the first row that matches:

| The code ... | Write |
|---|---|
| is a database table | `SQLModel` with `table=True` |
| is a request or response body | Pydantic `BaseModel` |
| reads settings from the environment | Pydantic `BaseSettings` |
| is a fixed set of named values | `StrEnum` in `src/domain/` (OOP-1) |
| holds domain data | `@dataclass(frozen=True)` in `src/domain/` (OOP-1) |
| groups configuration values for one class | `@dataclass(frozen=True)` next to that class |
| describes a dependency we want to swap or fake in tests | `Protocol` (OOP-5) |
| holds collaborators or configuration and carries out a use case | A class with an explicit `__init__` (OOP-2) |
| holds long-lived mutable state (a lock, subscribers, counters) | A class with an explicit `__init__` (OOP-2) |
| does none of the above | A module-level function; in `src/domain/` if it is pure domain logic |

A class with no state and a single method is usually a function. A function
can be injected too: type the parameter as a `Callable`. Whether a stateless
class may be injected as a strategy, as `IntervalBuilder` is today, is an
open decision (section 7).

## 2. Layers: where code goes

`<version>` is the API version, currently `v2`. The folder names are
proposals (section 7).

| Layer | Folder | Shape | May import from the project |
|---|---|---|---|
| Domain | `src/domain/` | Frozen dataclasses (including commands), `StrEnum`s, pure functions, the base error and shared protocols | Only `src/domain/` |
| Table models | `src/db/models/` | `SQLModel` classes with `table=True` | `domain` |
| Engine | `src/db/engine.py` | Creates the database engine and the session factory | `db.models` |
| Repositories | `src/db/repository/` | A module of `async` functions taking `session` first | `domain`, `db.models` |
| Startup loaders | `src/db/loaders/` | `async` functions that load reference data files into tables at startup | `domain`, `db.models` |
| Services | `src/services/` | Classes that receive collaborators and configuration and carry out use cases | `domain`, `db.repository` |
| Publishers | `src/publishers/` | Classes that implement a publishing protocol and fan out domain reports, for example to SSE clients | `domain` |
| Background components | `src/background/` | Classes that run a use case outside a request: clock ticks and updaters | `domain`, `services` |
| API schemas | `src/api/<version>/schemas/` | Pydantic `BaseModel`s with conversion methods | `domain` |
| Presenters | `src/api/<version>/presenters/` | Classes that build response schemas and need extra state | `domain`, `api` schemas |
| Dependency providers | `src/api/<version>/dependencies.py` | Functions that hand routers their session, services, publishers, background components and clock | `domain`, `db.engine`, `services`, `publishers`, `background` |
| Routers | `src/api/<version>/routers/` | Thin `async` functions | Everything above except `db.models` |
| Composition root | `src/main.py` (`lifespan`) | Builds every long-lived object once | Everything |

What each layer must not do:

- **Domain** does no I/O and never reads the clock. Domain logic is never
  `async`; a protocol in `src/domain/ports.py` may declare `async` methods.
- **Table models and schemas** contain no business rules.
- **Repositories and startup loaders** hold no state between calls.
- **Services, repositories and startup loaders** never commit (BE-2).
- **Services** work with domain objects. They never import table models or
  schemas, so table models stay inside `src/db/` and schemas stay inside
  `src/api/`.
- **Routers** contain no business rules and do not build objects field by
  field. A router converts the request with `to_domain()`, calls a service
  or repository, commits if it wrote anything, publishes, converts the
  result with `from_domain()` and returns it (OOP-4, BE-2). Committing and
  publishing are orchestration, not business rules.

A router may call a repository directly for a plain read or write that has
no business rule. Do not write a service that only passes calls through to a
repository.

Repositories stay as modules of functions. They have no state of their own,
so a class would only add a constructor around the session.

## 3. Terms

| Term | Meaning |
|---|---|
| Domain object | A plain Python object for something in the metro domain, such as a patrol session or a time span. It knows nothing about the database or the API. |
| Command | A frozen domain dataclass holding what a client asked for, before the server adds IDs and timestamps. |
| Use case | One thing the system does for a caller, such as "start a patrol session". |
| Collaborator | Another object a class calls to do its job, passed in through `__init__`. |
| Protocol (port) | A `typing.Protocol` that describes what a dependency must be able to do. Shared ones live in `src/domain/ports.py`. |
| Strategy | A swappable piece of behaviour passed into a class. |
| Presenter | A class that builds a response schema when the domain object alone is not enough. |
| Composition root | The one place that builds every long-lived object: `lifespan` in `src/main.py`. |

## 4. Rules

## Part A: classes and patterns

### OOP-1 Domain objects are frozen dataclasses with behaviour

Every entity that leaves `src/db/` is a domain object, even before it has
any methods. Domain objects use `@dataclass(frozen=True)`. Logic that only
needs the object's own fields belongs on the object as a method, and derived
values are `@property`. Logic that spans several domain objects is a pure
function in `src/domain/`. The current time is passed in as `now`, never
read inside the domain (BE-3). Shortened from `src/domain/coverage.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TimeSpan:
    """A closed time range ``[start, end]`` during which an area is covered."""

    start: datetime
    end: datetime

    def touches(self, other: TimeSpan) -> bool:
        """Return True if the spans overlap or share an endpoint."""
        return not (self.end < other.start or other.end < self.start)
```

Prefer immutable field types: `tuple` and `frozenset` instead of `list`,
`dict` and `set`. `frozen=True` only stops reassigning a field; a `list`
field can still be changed with `append`. Immutable fields are required
when the object is used as a dict key, put in a set, or shared between
tasks, because a mutable field makes hashing fail.

To change a frozen object, build a new one with `dataclasses.replace`.

A value with a fixed set of options is a `StrEnum` in `src/domain/`. Compare
against members (`EventType.CONNECT_EVENT`), never against raw strings
(`"connect"`).

Why: immutable objects can be shared and compared safely. Keeping table
models out of the domain means a column change does not ripple through
services. Passing `now` in keeps calculations deterministic in tests.

### OOP-2 Classes with collaborators or state use an explicit `__init__`

This applies to services, background components, publishers and
presenters. The class receives its collaborators and configuration through
`__init__` and stores them as `_private` attributes. It never builds its own
collaborators and never stores a database session (BE-2).

```python
class CoverageService:
    """Build coverage reports for every patrol area, grouped by station."""

    def __init__(self, builder: IntervalBuilder, rule: CoverageWindow) -> None:
        self._interval_builder = builder
        self._rule = rule
```

Do not use `@dataclass` for these classes.

If a constructor keeps growing, the class probably does too much and should
be split. Configuration values may be grouped in one frozen dataclass
(section 1); collaborators may not.

Why: a dataclass generates `__eq__` and `__repr__`, which mean nothing for a
service, and `_`-prefixed dataclass fields become `_`-prefixed constructor
keywords (`TrainManningService(_evaluator=...)`).

### OOP-3 Python basics

- **Attributes and properties, not getters and setters.** Do not write
  `get_x()` and `set_x()` methods that only read or write an attribute.
  Expose the attribute, or use `@property` when the value is computed. A
  property must be cheap and free of side effects; anything that does I/O,
  is `async` or is expensive is a method.
- **Privacy is a single underscore.** Prefix internal attributes, methods
  and module functions with `_`. Do not use `__name`: name mangling only
  helps against clashes in subclass hierarchies, which OOP-6 keeps shallow.
  Prefer testing through public behaviour over reading `_attributes`.
- **Private helpers are module functions.** A helper that does not use
  `self` is a module-level `_function`, not a `@staticmethod`. If two
  modules need it, it is no longer private: make it a method of the domain
  object it works on, or move it to a shared module and drop the
  underscore. Never create a base class only to share helpers.
- **Alternative constructors are `@classmethod`s** named `from_...`, such as
  `from_file` or `from_domain`.
- **Type hints.** Annotate every public function, method and attribute.
  Use modern syntax (`X | None`, `list[...]`, `collections.abc`) and spell
  out element types instead of a bare `tuple` or `dict`. Return `Self` when
  the method returns `self`, `cls(...)` or `dataclasses.replace(self, ...)`;
  when it returns `ClassName(...)`, use the class name.

### OOP-4 Conversions happen at the layer boundary

Each conversion has exactly one place. The outer layer does it, because the
inner layer must not know about the outer one.

| From | To | Where |
|---|---|---|
| Table row | Domain object | Repository function |
| Domain object | Table row | Repository function |
| Request schema | Command | `to_domain()` method on the request schema |
| Domain object | Response schema | `from_domain()` classmethod on the response schema |
| Domain object plus startup data | Response schema | Presenter |

Repository functions take and return domain objects. Table models never
leave `src/db/`.

`to_domain()` returns a command that holds only what the client sent. The
service adds server-generated IDs and the current time from the injected
clock (BE-3).

Routers call these conversions instead of doing them, so they stay thin.
Illustrative example:

```python
@router.post("/patrol-session/start", status_code=status.HTTP_201_CREATED)
async def start_patrol_session(
    body: PatrolSessionRequest,
    session: AsyncDbSessionDep,
    patrol_sessions: PatrolSessionServiceDep,
) -> StoredEventResponse:
    """Record that a steward started a patrol session."""
    event = await patrol_sessions.start(session, body.to_domain())
    await session.commit()
    return StoredEventResponse.from_domain(event)
```

A presenter is only needed when building the response needs more than the
domain object, such as station names loaded once at startup. Otherwise use
`from_domain()`.

Validation follows the same split. The request schema checks the shape and
format of what the client sent. A domain object checks its own invariants in
`__post_init__`. A service checks rules that need the database or other
objects.

### OOP-5 Interfaces are `Protocol`s

When a class depends on something we want to swap or fake, type the
dependency as a `typing.Protocol`. Put it in `src/domain/ports.py` when the
code using it and the implementations live in different layers, so both
sides can import it.

Recommended: implementations inherit from the protocol explicitly, and
methods that implement a protocol method or override a parent method are
marked with `@override` from `typing`. The type checker then reports a
missing or renamed method where the class is defined, instead of failing
silently or far away. `__init__` does not need `@override`.

```python
# src/domain/ports.py
class CoveragePublisher(Protocol):
    """Anything that can receive the latest coverage reports."""

    def publish(self, coverage: list[StationCoverageReport]) -> None:
        """Deliver the latest coverage reports without blocking."""
        ...


# src/publishers/sse_coverage.py
class SseCoverageBroadcaster(CoveragePublisher):
    """Push coverage reports to every connected SSE client."""

    @override
    def publish(self, coverage: list[StationCoverageReport]) -> None:
        """Queue the reports for each subscriber without waiting."""
        ...
```

Use an `abc.ABC` only when the implementations must share code.

### OOP-6 Prefer composition to inheritance

Inherit from framework and standard library classes (`SQLModel`,
`BaseModel`, `BaseSettings`, `Exception`, `StrEnum`, our protocols) when they
require it. Our own class hierarchies are at most one level deep and only
model a real "is a" relationship. To reuse behaviour, pass in an object that
has it. Exceptions may be grouped one level deeper (BE-5).

API schemas never inherit from table models, even though the SQLModel
documentation shows that pattern. Schemas declare their own fields.

Why: the API follows the versioned contracts in `contracts/`. A schema that
inherits from a table model changes the published API whenever a database
column changes.

## Part B: backend conventions

### BE-1 Wiring: build in `lifespan`, inject with `Depends`

Every service, background component and publisher is long-lived: it is
built once in `lifespan` in `main.py`. This works because none of them
holds a session (BE-2).

Routers receive these objects through a provider in
`src/api/<version>/dependencies.py` and an `Annotated[..., Depends(...)]`
alias. The provider is the only code that reads `request.app.state`. The
clock reaches routers the same way.

Why: FastAPI then documents and type-checks the dependency, and tests can
replace it with `app.dependency_overrides`.

### BE-2 Sessions and transactions

- Service methods that use the database take `session: AsyncSession` as
  their first argument, like repository functions. Services never store a
  session.
- Routers get the session from `AsyncDbSessionDep` and pass it on.
- Background components receive a session factory from `lifespan` and open
  one session per run.
- Services, repositories and startup loaders never commit. Repositories may
  call `flush()` when they need values the database generates.
- The outermost caller commits: the router for a request, or the background
  component for one run. `lifespan` commits once after all startup loaders
  have run.
- A use case commits at most once. A read-only use case does not commit.
- Publish, broadcast or notify (for example to the SSE stream) only after
  the commit has succeeded.

If an error is raised before the commit, the session closes without
committing and nothing from that use case is saved. A router that writes
and forgets to commit loses the write without an error, so tests for write
endpoints check that the data was stored.

Why: only the outermost caller knows where a use case ends, so services can
call each other without saving half a use case. Publishing after the commit
means listeners never see data that was rolled back. Keeping the session out
of `__init__` lets one instance serve both requests and background runs.

### BE-3 Time comes from an injected clock

Only the composition root reads the real clock. It passes a
`clock: Callable[[], datetime]` to every service, background component and
presenter that needs the current time, and to the clock provider.

- Domain objects take `now` as an argument (OOP-1).
- Services, background components, presenters and routers call the
  injected clock, never `datetime.now()`.
- The clock returns timezone-aware UTC times.

Why: tests can set the time, and every part of a calculation agrees on what
"now" is.

### BE-4 Async

- Routes, FastAPI dependencies and implementations of `async` protocol
  methods are always `async def`. FastAPI runs a plain `def` route or
  dependency in a worker thread, where `asyncio` objects such as queues and
  locks are not safe to use.
- Other functions are `async def` only if they await something.
- Blocking calls (`time.sleep`, synchronous file or network I/O, long CPU
  loops) are allowed only in `lifespan` before `yield`, including the
  startup loaders it calls, because no requests are served yet. Anywhere
  else, move them to a thread with `asyncio.to_thread`. That keeps the
  event loop responsive; it does not make CPU work faster.
- Background tasks are started in `lifespan`, kept in a variable, and
  cancelled and awaited on shutdown.
- Use an `asyncio.Lock` when a method reads shared state, awaits, and then
  relies on that state still being the same.

Why: one blocking call stops every request and every SSE stream, because
they all share one event loop.

### BE-5 Exceptions

- Errors that a caller is expected to handle, or that should become an HTTP
  response, inherit from `ManningPatrolError` in `src/domain/errors.py`. It
  lives in the domain so every layer can import it.
- Such errors may be grouped under shared classes such as `NotFoundError`,
  defined next to the base.
- A programming mistake or broken invariant that should never happen may
  raise a built-in exception such as `ValueError`. The client gets a 500.
- Specific exceptions are defined in the module that raises them, and their
  names end in `Error` (PEP 8).
- Exceptions know nothing about HTTP. The mapping from exception class to
  HTTP status is one table in `src/api/<version>/errors.py`, and each entry
  is registered with `app.add_exception_handler`. Starlette uses the
  handler of the closest parent class, so a subclass gets its parent's
  status unless it has its own entry.
- Do not override `__init__` only to store the message. `Exception` already
  does this; read it with `str(error)`.
- When translating one exception into another, use `raise ... from`.
- Catch specific exceptions. `except Exception` is allowed only in
  top-level background loops that log the error and keep running.

```python
# src/domain/errors.py
class ManningPatrolError(Exception):
    """Base class for errors raised by the backend's own code."""


class NotFoundError(ManningPatrolError):
    """Something the request refers to does not exist."""


# src/services/event_producer.py
class EventValidationError(ManningPatrolError):
    """An event or adjustment breaks a validation rule."""


class TargetEventNotFoundError(NotFoundError):
    """An adjustment targets an event that does not exist."""


# src/api/<version>/errors.py
HTTP_STATUS: dict[type[ManningPatrolError], int] = {
    EventValidationError: 400,
    NotFoundError: 404,
}
```

## 5. Review checklist

- [ ] The code is in the right layer and imports only what section 2 allows.
- [ ] Each new class matches a row in section 1; otherwise it is a function.
- [ ] Domain objects are frozen dataclasses and never read the clock (OOP-1, BE-3).
- [ ] Classes receive collaborators through `__init__` and never store a session (OOP-2, BE-2).
- [ ] Routers are thin: conversions use `to_domain()`, `from_domain()` or a repository (OOP-4).
- [ ] A write commits once, in the router or background run, and publishing happens after the commit (BE-2).
- [ ] No blocking calls in async code outside `lifespan` startup (BE-4).
- [ ] New exceptions inherit from `ManningPatrolError`, and HTTP statuses live only in the mapping table (BE-5).

## 6. Tooling

`uv run check` enforces part of this guideline: Ruff's `N` rules check
naming, Ruff's `B` rules catch several class pitfalls, and the type checker
checks type hints and protocol implementations. The rest is enforced in
review. Further Ruff rules are an open decision (section 7).

## 7. Open decisions

This draft makes a choice on each point below. The team should confirm or
change them before the status moves to Accepted.

1. **Constructor style (OOP-2).** Chosen: explicit `__init__`. Alternative:
   `@dataclass` with public fields.
2. **Explicit protocol inheritance (OOP-5).** Chosen: recommended, not
   required. Alternatives: required, or purely structural protocols.
3. **Stateless strategy classes (section 1).** Chosen: allowed when
   injected, as `IntervalBuilder` is today. Alternative: always functions,
   injected as callables.
4. **Who commits (BE-2).** Chosen: the router or background run, because
   publishing must follow the commit and that is the one place that sees
   both. Alternative: a session dependency that commits after the route
   returns, which removes the forgotten-commit risk but makes
   publish-after-commit harder.
5. **A domain object for every entity (OOP-1).** Chosen: yes, so table
   models stay in `src/db/` and one rule covers every case. Alternative:
   domain objects only where there is behaviour, with table models passed
   through elsewhere.
6. **Folder and file names (section 2).** Proposed locations:

   | What | Proposed location |
   |---|---|
   | Base error and group errors | `src/domain/errors.py` |
   | Shared protocols | `src/domain/ports.py` |
   | Engine and session factory | `src/db/engine.py` |
   | Startup loaders | `src/db/loaders/` |
   | Publishers and broadcasters | `src/publishers/` |
   | Background components | `src/background/` |
   | Presenters | `src/api/<version>/presenters/` |
   | HTTP error mapping | `src/api/<version>/errors.py` |
   | Dependency providers | `src/api/<version>/dependencies.py` (exists) |

7. **Further Ruff rules (section 6).** Candidates: `D` (docstrings, PEP 257
   convention), `SLF001` (private access), `RUF009` and `RUF012` (mutable
   class defaults), `PLR0913` (too many arguments), `FBT` (boolean flag
   arguments), `BLE001` (`except Exception`) and `TID251` (banned imports
   per layer). Each reports existing code, so each is a separate decision.
8. **Recording the decision.** Once Accepted, change the status here and
   write a short ADR that records the adoption and links to the commit
   where this file was accepted, so the ADR points at a fixed version.

## 8. Sources

There is no single PEP for object-oriented Python. Where the sources below
disagree, the PEPs win. The choices in section 7 are our own.

| Source | Used for |
|---|---|
| [PEP 8](https://peps.python.org/pep-0008/), "Designing for Inheritance" and "Naming Conventions" | Public and non-public names, getters and setters, exception naming |
| [Python tutorial, Classes](https://docs.python.org/3/tutorial/classes.html) | Privacy by convention, name mangling |
| [PEP 557](https://peps.python.org/pep-0557/) | Dataclasses |
| [PEP 544](https://peps.python.org/pep-0544/), [PEP 3119](https://peps.python.org/pep-3119/) | Protocols and abstract base classes |
| [PEP 673](https://peps.python.org/pep-0673/), [PEP 698](https://peps.python.org/pep-0698/) | `Self` and `@override` |
| [Python tutorial, user-defined exceptions](https://docs.python.org/3/tutorial/errors.html#user-defined-exceptions) | Exception hierarchy |
| [asyncio, developing with asyncio](https://docs.python.org/3/library/asyncio-dev.html) | Blocking calls in async code |
| [FastAPI, concurrency and async / await](https://fastapi.tiangolo.com/async/) | Which routes and dependencies run in a worker thread |
| [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) | Properties, `@staticmethod` and `@classmethod` |
| [Architecture Patterns with Python](https://www.cosmicpython.com/) | Background for layers, repositories and services. We differ: repositories are functions and the router commits. |
| Jack Diederich, *Stop Writing Classes* (PyCon 2012); Raymond Hettinger, *Python's Class Development Toolkit* (PyCon 2013) | Background on when a class is worth having |

We use only the standard library plus FastAPI, Pydantic and SQLModel. We do
not add `attrs`, a dependency injection container, or Pydantic for domain
objects, because each duplicates something we already have.
