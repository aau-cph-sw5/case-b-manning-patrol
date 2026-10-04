# AGENTS.md

Instructions for AI coding agents working in this repository. Humans: see
[CONTRIBUTING.md](CONTRIBUTING.md) and the [semester docs hub](https://github.com/aau-cph-sw5/semester-docs).

## Project

Metro "manning/patrol" compliance system: documents that trains are manned >= 70%
of running time and every station level is patrolled hourly.

```
contracts/                        versioned interfaces other teams build against
docs/adr/                         architecture decision records
manning-patrol-backend/           Python 3.13 / FastAPI, uv
manning-patrol-android-frontend/  Expo SDK 57 / React Native steward app
manning-patrol-desktop-frontend/ Vite + React 19 + TypeScript dashboard
```

## Global rules

1. **Use the real toolchain. Never improvise a substitute.** The backend needs
   `uv` — never work around a missing `uv` with pip/venv/`PYTHONPATH=src`; stop
   and have it installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`).
   Same for `npm` on the frontends. A hack that runs locally but not in CI is
   a bug, not a solution.
2. **Verify with the sub-repo's full check command before claiming anything
   works.** `uv run check` fails at the first broken stage; green lint does not
   mean tests ran.
3. **Stay inside your assigned issue.** One backlog item per feature branch.
   Never implement other items "while in there" or delete teammates' code.
4. **Never commit:** virtual environments, caches (`__pycache__`,
   `.pytest_cache`, `.ruff_cache`), `requirements.txt`, secrets, or anything
   Metro supplied. This repository is public.
5. **Match existing style.** Python: ruff, line length 88, double quotes,
   trailing commas (`uv run ruff format`). No AI-sounding comments.
6. **Update docs in the same branch as the code.** If a change alters a
   command, interface, or structure a README/ADR describes, update it in the
   same PR — never "later". Docs lagging merged code is how drift starts.
7. **Dev servers belong to humans too.** An occupied port is probably a
   human's server: verify against it; never kill processes you did not start.
   Leave dev servers running when your turn ends.

## Backend (manning-patrol-backend)

```bash
uv run check    # CI parity: uv sync --locked, ruff check, ty check,
                # ruff format --check, pytest. Run before pushing.
uv run ruff format .   # fix formatting before check complains
uv run dev      # dev server, localhost:8000
uv run positioning-simulator
```

- Deps via `uv add <pkg>` only; `uv.lock` is committed and CI uses
  `uv sync --locked`, so keep it in sync.
- Tests in `tests/`, synthetic fixtures in `fixtures/`.
- Lint rules: E, W, F, I, N, UP, B. Modern syntax (py313): `X | None`,
  `dict[...]`, `datetime.UTC`, sorted imports.

## Android frontend (manning-patrol-android-frontend)

Also read `manning-patrol-android-frontend/AGENTS.md`. Expo versions move
fast: check the versioned docs (https://docs.expo.dev/versions/v57.0.0/)
before using an API.

```bash
npm install && npm start   # expo start
npm run lint               # expo lint
```

CI runs `npm ci && npm run build --if-present && npm test --if-present` on
Node 20 and 22; adding a `test` script makes CI run it.

## Desktop frontend (manning-patrol-desktop-frontend)

```bash
npm install
npm run dev     # vite
npm run build   # tsc -b && vite build — the type check lives here
npm run lint    # oxlint
```

- Do not bypass `tsc -b` with `vite build` alone.
- React Compiler is enabled; do not add manual memoization without checking
  whether the compiler already handles it.

## Contracts and docs

- `contracts/` are published, versioned interfaces. Other teams build against
  them: add `v2/`, never edit a published version in place.
- `docs/adr/` ADRs are immutable: supersede with a new numbered ADR linking
  what it replaces. Only the Status field may change
  (Proposed -> Accepted -> Superseded).

## Branches and commits

- `main` protected (demonstrated work only); `development` is integration; one
  feature branch per backlog item (e.g. `feature/met-b-004-...`).
- Commit messages: short imperative summary, body explaining why. Scope
  commits to your task's files.
- Never push to `main` or force-push shared branches.
