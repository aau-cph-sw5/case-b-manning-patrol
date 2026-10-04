# AGENTS.md

Instructions for AI coding agents (Mistral Vibe, Claude Code, etc.) working in this
repository. Human contributors: see [CONTRIBUTING.md](CONTRIBUTING.md) and the
[semester docs hub](https://github.com/aau-cph-sw5/semester-docs).

## Project overview

Compliance-grade system for the Metro "manning/patrol" requirement: it documents that
trains are manned at least 70 percent of running time and that every station level is
patrolled at least once per rolling sixty minutes. Three deployables plus published
contracts:

```
contracts/                        versioned interfaces other teams build against
docs/adr/                         architecture decision records (ADRs)
manning-patrol-backend/           Python 3.13 / FastAPI, managed by uv
manning-patrol-android-frontend/  Expo (SDK 57) / React Native app for stewards
manning-patrol-desktop-frontend/  Vite + React 19 + TypeScript control-room dashboard
```

## Global rules for agents

1. **Use the project's real toolchain. Never improvise a substitute.**
   The backend is managed by `uv`. Do not work around a missing `uv` with
   `pip`, `venv`, `PYTHONPATH=src`, or similar. If `uv` is not installed, stop and
   tell the user to run `curl -LsSf https://astral.sh/uv/install.sh | sh`.
   The same applies to `npm` for the frontends. A hack that runs tests on your
   machine but not in CI is a bug, not a solution.

2. **Run the check command before claiming anything works.**
   Before you say a change is done, run the sub-repo's full check command (below)
   and read its output. "The tests passed when I ran pytest manually" is not
   verification. `uv run check` fails at the first broken stage, so a green
   lint does not mean the type check, format check, or tests ran.

3. **Stay inside your assigned task.**
   Each backlog item is one GitHub issue, one feature branch. Do not implement
   another item "while you are in there", and never delete a teammate's code or
   tests unless your task explicitly requires it.

4. **Never commit:**
   virtual environments, `__pycache__`, `.pytest_cache`, `.ruff_cache`,
   `requirements.txt` (dependencies live in `pyproject.toml`/`uv.lock`),
   secrets, or anything Metro Service supplied. This repository is public.

5. **Match existing style.** Python: ruff, line length 88, double quotes,
   trailing commas (run `uv run ruff format`). Keep code free of AI-sounding
   comments and docstrings; comments describe behavior, not deliberation.

6. **Update documentation in the same branch as the code.** If you change a
   command, an interface, the project structure, or behavior a README/ADR
   describes, update that document in the same PR — never "after review" or
   "later". Reviewers must see code and docs together; docs lagging behind
   merged code is how drift starts. CI passing is the precondition for the
   whole branch, docs included.

7. **Dev servers belong to humans too.** If a port is already in use, assume
   a human is running the server there: verify your changes against the
   running instance (or ask), and never kill a process you did not start to
   free the port. Leave dev servers running when you finish a task; do not
   close them just because your turn is over.

## Backend — manning-patrol-backend

Python 3.13, FastAPI, pydantic, `src/` layout, uv for everything.

Commands (run from `manning-patrol-backend/`):

```bash
uv run check    # FULL CI PARITY: uv sync --locked, ruff check, ty check,
                # ruff format --check, pytest. Run this before pushing.
uv run lint     # ruff check + ty check only
uv run ruff format .   # fix formatting before check complains
uv run dev      # dev server (auto-reload, localhost:8000)
uv run positioning-simulator  # positioning interface simulator
```

- Dependency groups: runtime deps in `pyproject.toml`, `pytest`/`ruff`/`ty` in the
  dev group. Add deps with `uv add <pkg>`, never by editing files by hand only.
- `uv.lock` is committed; CI installs with `uv sync --locked`, so the lockfile
  must stay in sync with `pyproject.toml`.
- Tests live in `tests/`, fixtures in `fixtures/` (synthetic data only).
- Lint rules: E, W, F, I, N, UP, B. Python version target py313: use modern
  syntax (`X | None`, `dict[...]`, `datetime.UTC`), sorted imports.

## Android frontend — manning-patrol-android-frontend

Expo SDK 57 / React Native 0.86 / React 19, expo-router. Also read
[AGENTS.md](manning-patrol-android-frontend/AGENTS.md) in this directory.

```bash
npm install
npm start       # expo start
npm run lint    # expo lint
```

- CI runs `npm ci && npm run build --if-present && npm test --if-present` on
  Node 20 and 22. If you add a `build` or `test` script, CI will run it.
- Expo versions move fast: check the exact versioned docs
  (https://docs.expo.dev/versions/v57.0.0/) before using an API.

## Desktop frontend — manning-patrol-desktop-frontend

Vite + React 19 + TypeScript, oxlint for linting. No test runner yet.

```bash
npm install
npm run dev     # vite dev server
npm run build   # tsc -b && vite build (type check happens here)
npm run lint    # oxlint
```

- `npm run build` is the type check: `tsc -b` fails on type errors. Do not
  bypass it with `vite build` alone.
- React Compiler (babel-plugin-react-compiler) is enabled; do not add manual
  memoization without checking whether the compiler already handles it.

## Contracts and docs

- `contracts/` contains published, versioned interfaces
  (`positioning-interface/v1`, `positioning-ingestion/v1`). Other teams build
  against these. Changes must be additive: add `v2/`, never edit a published
  version in place.
- `docs/adr/` holds architecture decisions. Non-trivial design choices get a
  new numbered ADR, not a silent code change. ADRs are immutable: never edit an
  existing ADR — add a new numbered one that links to the ADR it supersedes.
  The Status field is the only thing you may update (Proposed → Accepted →
  Superseded).

## Branches and commits

- `main` is protected: only what has been demonstrated at a review. `development`
  is the shared integration branch. One feature branch per backlog item, named
  after it (e.g. `feature/met-b-004-presence-and-patrol-record-capture`).
- Commit messages: short imperative summary, optionally a body explaining why.
  Scope the commit to files belonging to your task.
- Never push to `main` or force-push shared branches.
