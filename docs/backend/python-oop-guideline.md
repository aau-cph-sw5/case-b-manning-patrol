# Python OOP guideline for the backend

**Status:** Draft, proposed for team agreement
**Applies to:** `services/api`
**Last updated:** 2026-11-02

This guideline describes how we write object-oriented code in the backend.
It follows Python's own conventions, not Java or C#. In Python a class is one
tool next to modules and functions, and a module of functions is often the
more Pythonic choice.

The goal is predictability: a developer from another group should be able to
guess where a piece of logic lives and what shape it has before opening the
file.

Terms such as *value object*, *service* and *entry point* are defined in the
[glossary](glossary.md). Docstring and formatting rules are in
[AGENTS.md](../../AGENTS.md) and are not repeated here.

Rules are numbered (`OOP-1`, `OOP-2`, ...) so they can be referenced in
pull request reviews.

## Contents

1. [Sources](#1-sources)
2. [Layers: where code goes](#2-layers-where-code-goes)
3. [When to write a class](#3-when-to-write-a-class)
4. [Rules](#4-rules)
5. [Review checklist](#5-review-checklist)
6. [Tooling](#6-tooling)
7. [Libraries we do not adopt](#7-libraries-we-do-not-adopt)
8. [Open decisions](#8-open-decisions)

## 1. Sources

There is no single PEP for object-oriented Python. This guideline is built
from the following sources; where they disagree, the PEPs win.

| Source | Used for |
|---|---|
| [PEP 8](https://peps.python.org/pep-0008/), "Designing for Inheritance" and "Naming Conventions" | Public and non-public names, no trivial getters and setters, exception naming |
| [PEP 257](https://peps.python.org/pep-0257/) | Class and method docstrings |
| [Python tutorial, Classes](https://docs.python.org/3/tutorial/classes.html) | Privacy by convention, name mangling |
| [PEP 557](https://peps.python.org/pep-0557/) | Dataclasses |
| [PEP 544](https://peps.python.org/pep-0544/), [PEP 3119](https://peps.python.org/pep-3119/) | Protocols and abstract base classes |
| [PEP 673](https://peps.python.org/pep-0673/), [PEP 698](https://peps.python.org/pep-0698/) | `Self` and `@override` |
| [Python tutorial, user-defined exceptions](https://docs.python.org/3/tutorial/errors.html#user-defined-exceptions) | Exception hierarchy |
| [asyncio, developing with asyncio](https://docs.python.org/3/library/asyncio-dev.html) | Blocking calls in async code |
| [FastAPI, concurrency and async / await](https://fastapi.tiangolo.com/async/) | Which routes and dependencies run in a worker thread |
| [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html), sections 2.13 and 2.17 | Properties, `@staticmethod` and `@classmethod` |
| [Architecture Patterns with Python](https://www.cosmicpython.com/) | Repository, service layer and unit of work in Python |
| Jack Diederich, *Stop Writing Classes* (PyCon 2012); Raymond Hettinger, *Python's Class Development Toolkit* (PyCon 2013) | When a class is worth having |

## 2. Layers: where code goes

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
| API schemas | `src/api/v2/schemas/` | Pydantic `BaseModel`s with conversion methods | `domain` |
| Presenters | `src/api/v2/presenters/` | Classes that build response schemas and need extra state | `domain`, `api` schemas |
| Dependency providers | `src/api/v2/dependencies.py` | Functions that hand routers their session, services, publishers, background components and clock | `domain`, `db.engine`, `services`, `publishers`, `background` |
| Routers | `src/api/v2/routers/` | Thin `async` functions | Everything above except `db.models` |
| Composition root | `src/main.py` (`lifespan`) | Builds every long-lived object once | Everything |

The folder names are proposals (section 8).

What each layer must not do:

- **Domain** does no I/O and never reads the clock. Domain logic is never
  `async`; a protocol in `src/domain/ports.py` may declare `async` methods.
- **Table models and schemas** contain no business rules.
- **Repositories and startup loaders** hold no state between calls.
- **Services, repositories and startup loaders** never commit (OOP-11).
- **Services** only see domain objects. They never import table models or
  schemas, so table models stay inside `src/db/` and schemas stay inside
  `src/api/`.
- **Routers** contain no business rules and do not build objects field by
  field. A router converts the request with `to_domain()`, calls a service
  or repository, commits if it wrote anything, triggers any publishing,
  converts the result with `from_domain()` and returns it (OOP-7, OOP-11).

A router may call a repository directly for a plain read or write that has
no business rule. Do not write a service that only passes calls through to a
repository.

Repositories stay as modules of functions. They have no state of their own,
so a class would only add a constructor around the session.

## 3. When to write a class

Pick the first line that matches:

| The code ... | Write |
|---|---|
| holds domain data | `@dataclass(frozen=True)` in `src/domain/` (OOP-1) |
| groups configuration values for a class | `@dataclass(frozen=True)` next to that class |
| is a database table | `SQLModel` with `table=True` |
| is a request or response body | Pydantic `BaseModel` |
| is a fixed set of named values | `StrEnum` in `src/domain/` (OOP-1) |
| holds collaborators or configuration and carries out a use case | A service class (OOP-2) |
| holds long-lived mutable state (a lock, subscribers, counters) | A class with an explicit `__init__` (OOP-2) |
| does none of the above | A module-level function; in `src/domain/` if it is pure domain logic |

A class with no state and a single method is a function. The exception is a
class that is built in `lifespan` and injected as a swappable strategy, such
as `IntervalBuilder`. If nothing injects it, write a function.

When a class depends on something we want to swap or fake in tests, type
that dependency as a `Protocol` (OOP-8). The protocol describes the
dependency; the implementation is still chosen from the table above.

## 4. Rules

### OOP-1 Domain objects are frozen dataclasses with behaviour

Domain objects use `@dataclass(frozen=True)`. Logic that only needs the
object's own fields belongs on the object as a method, and derived values
are `@property`. Logic that spans several domain objects is a pure function
in `src/domain/`. The current time is passed in as `now`, never read inside
the domain (OOP-12). Shortened from `src/domain/coverage.py`:

```python
@dataclass(frozen=True)
class TimeSpan:
    """A closed time range ``[start, end]`` during which an area is covered."""

    start: datetime
    end: datetime

    def touches(self, other: TimeSpan) -> bool:
        """Return True if the spans overlap or share an endpoint."""
        return not (self.end < other.start or other.end < self.start)
```

Fields of a frozen dataclass are immutable types too: use `tuple` and
`frozenset`, never `list`, `dict` or `set`. `frozen=True` only stops
reassigning a field; a `list` field can still be changed with `append`, and
the object can no longer be hashed. Python 3.13 has no hashable frozen
mapping, so store key-value pairs as a tuple of pairs, for example
`tuple[tuple[AreaKind, timedelta], ...]`.

To change a frozen object, build a new one with `dataclasses.replace`.

A value with a fixed set of options is a `StrEnum` in `src/domain/`. Compare
against members (`EventType.CONNECT_EVENT`), never against raw strings
(`"connect"`).

Why: fully immutable objects can be shared, cached and compared safely, and
passing `now` in keeps the coverage calculation deterministic in tests.

### OOP-2 Classes with collaborators or state use an explicit `__init__`

This applies to services, background components, publishers and
presenters. The class receives its collaborators and configuration through
`__init__` and stores them as `_private` attributes. It never builds its own
collaborators and never stores a database session (OOP-11).

```python
class CoverageService:
    """Build coverage reports for every patrol area, grouped by station."""

    def __init__(self, builder: IntervalBuilder, rule: CoverageWindow) -> None:
        self._interval_builder = builder
        self._rule = rule
```

Do not use `@dataclass` for these classes.

A constructor with more than 6 parameters, not counting `self`, means the
class does too much and should be split. The clock and the session factory
count. Configuration values may be grouped in one frozen dataclass
(section 3); collaborators may not.

Why: most services already follow this form. A dataclass generates `__eq__`
and `__repr__`, which mean nothing for a service, and `_`-prefixed dataclass
fields become `_`-prefixed constructor keywords
(`TrainManningService(_evaluator=...)`).

### OOP-3 Attributes and properties instead of getters and setters

Do not write `get_x()` and `set_x()` methods that only read or write an
attribute. Expose the attribute, or use `@property` when the value is
computed. A property must be cheap and free of side effects. Anything that
does I/O, is `async` or is expensive is a method.

```python
# Do
@property
def manned_ratio(self) -> float | None: ...

# Don't
def get_manned_ratio(self) -> float | None: ...
```

### OOP-4 Privacy is a single underscore

Prefix internal attributes, methods and module functions with one
underscore. Do not use double underscores (`__name`). Python mangles those
names, which only helps against name clashes in subclasses.

Do not read another object's `_attributes` from outside its class, including
in tests. Test through behaviour instead: call public methods and check what
they return or what they cause. Add a public property only if real callers
would also use it, not just the test (OOP-3).

### OOP-5 Helpers are module functions, not `@staticmethod`

A private helper that does not use `self` is a module-level `_function` below
the class, not a `@staticmethod`.

If two modules need the same helper, it is no longer private:

- if it works on one domain object, make it a method of that object;
- otherwise, move it to a shared module and drop the underscore.

Never create a base class only to share helpers between services.

### OOP-6 Alternative constructors are `@classmethod`s

Constructors that build an object from another source are named `from_...`
and are `@classmethod`s. They build the object with `cls(...)`, so they
return `Self` (OOP-15).

```python
@classmethod
def from_file(cls, path: Path = SHIFTS_FILE) -> Self:
    """Load the night shift and its timezone from the shifts JSON file."""
```

### OOP-7 Conversions happen at the layer boundary

Each conversion has exactly one place. The outer layer always does it,
because the inner layer must not know about the outer one.

| From | To | Where |
|---|---|---|
| Table row | Domain object | Repository function |
| Domain object | Table row | Repository function |
| Request schema | Command | `to_domain()` method on the request schema |
| Domain object | Response schema | `from_domain()` classmethod on the response schema |
| Domain object plus startup data | Response schema | Presenter in `src/api/v2/presenters/` |

Repository functions take and return domain objects. Table models never
leave `src/db/`.

`to_domain()` returns a command: a frozen dataclass in `src/domain/` that
holds only what the client sent. The service adds server-generated IDs and
the current time from the injected clock (OOP-12).

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

### OOP-8 Interfaces are `Protocol`s

When a class depends on something we want to swap or fake, the dependency
is typed as a `typing.Protocol`. Define the protocol in the lowest layer
that both the code using it and every implementation may import
(section 2). When that is the domain, put it in `src/domain/ports.py`.

Implementations inherit from the protocol explicitly. Mark every method
that implements a protocol method or overrides a parent class method with
`@override` from `typing`. `__init__` does not need it.

```python
# src/domain/ports.py
class CoveragePublisher(Protocol):
    """Anything that can receive the latest coverage reports."""

    def publish(self, coverage: list[StationCoverageReport]) -> None:
        """Deliver the latest coverage reports without blocking."""
        ...


# src/publishers/sse_coverage.py
class SseCoverageBroadcaster(CoveragePublisher):
    @override
    def publish(self, coverage: list[StationCoverageReport]) -> None: ...
```

Why explicit inheritance: `ty` treats a protocol method with a `...` body as
abstract, so it reports an implementation that forgets a method as
`Cannot instantiate abstract class` (checked with ty 0.0.95).

Use an `abc.ABC` only when the implementations must share code.

### OOP-9 Prefer composition to inheritance

Inherit from framework and standard library classes (`SQLModel`,
`BaseModel`, `BaseSettings`, `Exception`, `StrEnum`, our protocols) when they
require it. Our own class hierarchies are at most one level deep and only
model a real "is a" relationship. To reuse behaviour, pass in an object that
has it.

The depth limit does not apply to exceptions. They may be grouped under
`ManningPatrolError`, for example `NotFoundError` (OOP-14).

API schemas never inherit from table models, even though the SQLModel
documentation shows that pattern. Schemas declare their own fields.

Why: the API follows the versioned contracts in `contracts/`. A schema that
inherits from a table model changes the published API whenever a database
column changes.

### OOP-10 Wiring: build in `lifespan`, inject with `Depends`

Every service, background component and publisher is long-lived: it is
built once in `lifespan` in `main.py`. This works because none of them
holds a session (OOP-11).

Routers receive these objects through a provider in
`src/api/v2/dependencies.py` and an `Annotated[..., Depends(...)]` alias.
The provider is the only code that reads `request.app.state`. The clock
reaches routers the same way, through a provider.

Why: FastAPI then documents and type-checks the dependency, and tests can
replace it with `app.dependency_overrides`.

### OOP-11 Sessions and transactions

- Service methods that use the database take `session: AsyncSession` as
  their first argument, like repository functions. Services never store a
  session.
- Routers get the session from `AsyncDbSessionDep` and pass it on.
- Background components receive a session factory from `lifespan` and open
  one session per run.
- Services, repositories and startup loaders never commit. Repositories may
  call `flush()` when they need values the database generates.
- The outermost caller commits: the router for a request, or the background
  component for one run. Startup loading is committed by `lifespan`
  (section 8).
- A use case commits at most once. A read-only use case does not commit.
- Publish, broadcast or notify (for example to the SSE stream) only after
  the commit has succeeded.

If an error is raised before the commit, the session closes without
committing and nothing from that use case is saved.

Why: only the outermost caller knows where a use case ends, so services can
call each other without saving half a use case. Publishing after the commit
means listeners never see data that was rolled back. Keeping the session out
of `__init__` lets one instance serve both requests and background runs.

### OOP-12 Time comes from an injected clock

Only the composition root reads the real clock. It passes a
`clock: Callable[[], datetime]` to every service, background component and
presenter that needs the current time, and to the clock provider in
`src/api/v2/dependencies.py`.

- Domain objects take `now` as an argument (OOP-1).
- Services, background components, presenters and routers call the
  injected clock, never `datetime.now()`.
- The clock returns timezone-aware UTC times.

Why: tests can set the time, and every part of a calculation agrees on what
"now" is.

### OOP-13 Async

- Routes, FastAPI dependencies and implementations of `async` protocol
  methods are always `async def`. FastAPI runs a plain `def` route or
  dependency in a worker thread, where `asyncio` objects such as queues and
  locks are not safe to use.
- Other functions are `async def` only if they await something.
- Blocking calls (`time.sleep`, synchronous file or network I/O, long CPU
  loops) are allowed only in `lifespan` before `yield`, including the
  startup loaders it calls, because no requests are served yet. Anywhere
  else, move them to a thread with
  `asyncio.to_thread`.
- Background tasks are started in `lifespan`, kept in a variable, and
  cancelled and awaited on shutdown.
- Use an `asyncio.Lock` when a method reads shared state, awaits, and then
  relies on that state still being the same.

Why: one blocking call stops every request and every SSE stream, because
they all share one event loop.

### OOP-14 Exceptions

- Every backend exception inherits from `ManningPatrolError`, defined in
  `src/domain/errors.py`. It lives in the domain because every layer,
  including the domain, must be able to import it (section 2).
- Errors may be grouped under shared classes such as `NotFoundError`. These
  group classes live next to the base in `src/domain/errors.py`.
- Specific exceptions are defined in the module that raises them, and their
  names end in `Error` (PEP 8).
- Exceptions know nothing about HTTP. The mapping from exception class to
  HTTP status is one table in `src/api/v2/errors.py`, used by a single
  handler for `ManningPatrolError`. The handler walks
  `type(error).__mro__` and the first class found in the table wins, so a
  subclass gets its parent's status unless it has its own row. An
  exception with no match answers 500.
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


# src/api/v2/errors.py
HTTP_STATUS: dict[type[ManningPatrolError], int] = {
    EventValidationError: 400,
    NotFoundError: 404,
}
```

### OOP-15 Type hints

Every public function, method and attribute is annotated. Use modern syntax:
`X | None`, `list[...]` and `collections.abc` for abstract types. Do not
return a bare `tuple` or `dict`; spell out the element types.

Use `Self` only when the method returns `self`, `cls(...)` or
`dataclasses.replace(self, ...)`. When it returns `ClassName(...)`, annotate
it with the class name; `ty` rejects `Self` there with
`invalid-return-type`. Python 3.13 evaluates annotations eagerly, so a class
naming itself needs `from __future__ import annotations` or quotes.

## 5. Review checklist

- [ ] The code is in the right layer and imports only what section 2 allows.
- [ ] Each new class has a reason from section 3; otherwise it is a function.
- [ ] Domain objects are frozen, have immutable fields, use enums instead of raw strings and do not read the clock (OOP-1).
- [ ] Classes get collaborators through `__init__`, store them as `_private`, hold no session and take at most 6 parameters (OOP-2, OOP-11).
- [ ] No trivial getters or setters (OOP-3).
- [ ] No `@staticmethod` for private helpers, and no copy-pasted helpers between modules (OOP-5).
- [ ] Conversions are in the repository or on the schema, not in routers or services (OOP-7).
- [ ] Protocols live in the lowest layer both sides may import; implementations and overrides use `@override` (OOP-8).
- [ ] Routers get services and the clock through `Depends`; only providers read `request.app.state` (OOP-10).
- [ ] Only the outermost caller commits, at most once, and publishing happens after the commit (OOP-11).
- [ ] No `datetime.now()` outside the composition root (OOP-12).
- [ ] Routes and dependencies are `async def`; no blocking calls outside `lifespan` startup (OOP-13).
- [ ] Exceptions inherit from `ManningPatrolError`, and HTTP statuses live only in the mapping table (OOP-14).
- [ ] `Self` is used only for methods that return `self`, `cls(...)` or `replace(self, ...)` (OOP-15).

## 6. Tooling

Enforced today by `uv run check`:

- `ruff` rule set `N` checks class, function and exception naming.
- `ruff` rule set `B` catches several class pitfalls, such as an abstract
  base class without abstract methods.
- `ty` type-checks protocol implementations and type hints, including
  missing protocol methods (OOP-8) and wrong uses of `Self` (OOP-15).

The rest of this guideline is enforced in review. Which further Ruff rules
to enable is an open decision (section 8).

## 7. Libraries we do not adopt

Everything in this guideline uses the standard library plus the FastAPI,
Pydantic and SQLModel we already have. The libraries below are often
recommended for object-oriented Python. We do not use them, because each one
would force a large rewrite or duplicate a tool we have:

| Library or pattern | Why not |
|---|---|
| `attrs` | Same job as `dataclasses` |
| `dependency-injector`, `punq`, `lagom` | Duplicate FastAPI's `Depends` |
| SQLAlchemy imperative mapping (from *Architecture Patterns with Python*) | Would mean rewriting every table model in `src/db/models/`; repositories converting rows to domain objects (OOP-7) gives the same separation |
| `returns` and other dry-python libraries | Functional style, the opposite direction of this guideline |
| Pydantic for domain objects | Domain objects stay plain dataclasses; Pydantic stays at the API boundary |

## 8. Open decisions

This draft makes a choice on the points below. The team should confirm or
change them before the status moves to Accepted.

1. **Constructor style (OOP-2).** Explicit `__init__`, chosen because most
   services already use it. Alternative: `@dataclass` with public fields.
2. **Explicit protocol inheritance (OOP-8).** Chosen because `ty` then
   catches missing methods. Alternative: purely structural protocols with
   no inheritance.
3. **Stateless strategy classes (section 3).** Allowed when injected.
   Alternative: always functions, injected as callables.
4. **Folder and file names (section 2).** Proposed locations:

   | What | Proposed location |
   |---|---|
   | Base error and group errors | `src/domain/errors.py` |
   | Shared protocols | `src/domain/ports.py` |
   | Engine and session factory | `src/db/engine.py` |
   | Startup loaders | `src/db/loaders/` |
   | Publishers and broadcasters | `src/publishers/` |
   | Background components | `src/background/` |
   | Presenters | `src/api/v2/presenters/` |
   | HTTP error mapping | `src/api/v2/errors.py` |
   | Dependency providers | `src/api/v2/dependencies.py` (exists) |

5. **Who commits startup loading (OOP-11).** Proposed default: `lifespan`
   commits once after all startup loaders have run.
6. **Further Ruff rules (section 6).** None of these are enabled. Enabling
   each one is a separate decision because it will report existing code.
   CI picks them up automatically from `pyproject.toml`.

   | Ruff rules | Checks |
   |---|---|
   | `D` with `convention = "pep257"`, ignoring `D105` and `D107` | Missing or badly formed docstrings. `D105` (dunder methods) and `D107` (`__init__`) are ignored because AGENTS.md does not require those docstrings. |
   | `SLF001` | Access to another object's `_private` members (OOP-4) |
   | `RUF009`, `RUF012` | Mutable or function-call defaults in classes and dataclasses |
   | `PLR0913`, with `max-args` set to match OOP-2's limit | Too many constructor or function arguments (OOP-2) |
   | `FBT` | Boolean flag arguments |
   | `BLE001` | `except Exception`; allowed spots get a `# noqa: BLE001` (OOP-14) |
   | `TID251` (banned-api) | Imports a layer is not allowed to make (section 2). Needs a `ruff.toml` per layer folder that extends the main configuration. Tested: it blocks submodule and relative imports too. |

7. **Recording the decision.** Once Accepted, write a short ADR in
   `docs/adr/` that records the adoption and links to this file. This file
   stays editable; the ADR does not copy it.
