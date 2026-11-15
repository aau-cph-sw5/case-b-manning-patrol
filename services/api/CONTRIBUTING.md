# Backend Rules

This document gives the rules for our backend code. All persons on the team must follow these rules.

## 1. Layer Rules

The code has three layers. The data moves in one direction only.

```text
Router → Service → Repository → Database
```

- `routers` imports from `services`.
- `services` imports from `repositories` .
- `repositories` imports from `models` only.



### Router

- A router does two things only: it reads the input data, and it calls one service method.
- A router does not do business logic.
- A router does not read from or write to the database directly.
- A router does not use `app.state` directly. Use the provider functions in `dependencies.py`.
- Routers are functions, not classes.

### Service

- A service holds the business logic.
- Services are classes only.
- One class per file is the rule of thumb. Small, related items can share a file.
- A service does not import anything from the router layer or from the API schemas.
- A service gets its helpers (repositories, other services) through the constructor (`__init__`), not through setters or global state.
- A service does not touch the database directly. It uses repository functions.

### Repository

- The database layer is a set of functions, not classes.
- Each function takes a session as the first argument.
- Write functions commit. Read functions do not commit.

## 2. Function Rules

- A function does one thing only.
- Keep a function short. Target: not more than about 20 lines (not including docstrings).
- Use not more than 4 real parameters. The session is not a real parameter.
- Always call parameters by keyword at the call site. Example: `greet(message="hello")`.
- If you need more than 4 parameters, make a frozen dataclass that holds the input data.

## 3. Class and Data Rules

### Classes

- Mark private functions and methods with a leading underscore (`_`).
- A method that does not use `self` and is static by nature gets the `@staticmethod` marker.
- A class that holds no state and uses no `__init__` is a dataclass. Mark it as such.
- A class holds state plus behavior. If a class holds fields only, make it a frozen dataclass.
- No module-level variables, only constants. App-level objects live on `app.state`.

### Where to build objects

Objects are built in two places only:

- The fastapi lifespan builds the objects that live as long as the application runs, e.g in `main.py`.
- Objects that live for one request are build in a common place, e.g `dependencies.py`.

Everywhere else, you get an object from the outside. You do not build it yourself:

- A router gets objects with `Depends()`. A router never builds an object.
- A service gets objects through the constructor (`__init__`).
- Do not make an object at module level. Do not use a global object.

One exception: a service can build a pure object inside itself. Pure means: no I/O, no config, no clock, no randomness, no shared state. The service keeps this object private. If a test must replace the object, then it is not pure. Build it in `main.py` or `dependencies.py` and inject it.

### Data

- Data has no logic: use `@dataclass(frozen=True)`.
- Pydantic models are used at the API edge only (request and response schemas).

## 4. Errors

- Each module has its own custom exception classes.
- Services raise exceptions. Routers convert exceptions to HTTP status codes in one place.
- Do not return `False` or error codes. `None` for "not found" is acceptable when the documentation says so.

## 5. Tests and Docs

- Write one docstring for each public function and class.
- Unit tests mirror the source structure: one test file per source module.
- Do not test private functions.