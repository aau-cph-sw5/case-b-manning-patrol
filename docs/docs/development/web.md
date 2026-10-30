# Web Dashboard

Control-room dashboard built with Vite + React 19 + TypeScript.

**Location:** `apps/web/`

## Prerequisites

- Node.js 20 or 22
- npm >= 11.4.2

## Running Locally

```bash
cd apps/web
npm install
npm run dev                      # Vite dev server
```

## Commands

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Vite dev server with HMR |
| `npm run build` | Type-check (`tsc -b`) + production build |
| `npm run lint` | Run oxlint |
| `npm test` | Run vitest tests |
| `npm run coverage` | Vitest with v8 coverage (fails below 80%) |

## Project Structure

```
apps/web/src/
├── App.tsx                      # Root component
├── main.tsx                     # Entry point
├── components/                  # UI building blocks
├── hooks/                       # React hooks
├── api/                         # API client layer
├── data/                        # Reference data, mock data
├── utils/                       # Utility functions
└── assets/                      # Static assets
```

## Key Technologies

- **React 19** with React Compiler enabled — do not add manual memoization
- **Vite** for dev server and build
- **TypeScript** strict mode — type check runs in `npm run build`
- **Oxlint** for linting
- **Vitest** for testing with v8 coverage

## Backend Connection

The dashboard connects to the backend API for:
- Real-time compliance status via **Server-Sent Events (SSE)**
- Historical records and coverage data via REST

Configure the API URL in the environment or settings file.

## Development Notes

- The type check lives in `npm run build` (`tsc -b`). Never bypass it with
  `vite build` alone.
- React Compiler is enabled — avoid manual `useMemo`/`useCallback` unless
  profiling shows a real need.
- Coverage threshold is 80% — `npm run coverage` fails below that.
