# Manning/Patrol Desktop Dashboard

> Control-room dashboard for the Manning/Patrol requirement system (Case B)

This is the **desktop web dashboard** component of the Manning/Patrol requirement system. It provides a real-time control-room interface for monitoring steward presence, patrol completion, and station coverage status across the Metro network.

## Overview

The dashboard is built with:
- **React 19** with React Compiler for optimized re-renders
- **TypeScript** for type safety
- **Vite 8** for fast development and production builds
- **Oxlint** for linting
- **Vitest** for testing with coverage thresholds

The dashboard consumes data from the [API service](../services/api) and displays:
- Real-time steward presence and activity status
- Patrol completion status per station
- Overdue and at-risk station indications
- Historical coverage records

## Prerequisites

- Node.js 20 or 22
- npm >= 11.4.2

## Getting Started

### Installation

```bash
cd ../apps/web
npm install
```

### Development

Start the Vite development server:

```bash
npm run dev
```

The app will be available at `http://localhost:5173/dashboard` (or next available port).

**Note:** The development server automatically proxies `/api` requests to `http://localhost:8000`. Make sure the [API service](../services/api) is running on port 8000 before starting the dashboard.

### Configuration

To connect to a different API endpoint, modify the proxy configuration in `vite.config.ts`:

```typescript
server: {
  proxy: {
    '/api': 'http://your-api-url:port',
  },
}
```

Or set the API base URL in `src/settings.ts`.

## Available Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Start Vite development server with hot reload |
| `npm run build` | Type-check and create production build |
| `npm run preview` | Preview production build locally |
| `npm run lint` | Run Oxlint on the codebase |
| `npm run test` | Run unit tests with Vitest |
| `npm run coverage` | Run tests with coverage report |

## Project Structure

```
apps/web/
├── src/
│   ├── App.tsx           # Root component
│   ├── Home.tsx          # Main dashboard view
│   ├── main.tsx          # Application entry point
│   ├── settings.ts       # Configuration (API URLs, etc.)
│   ├── api/              # API client and hooks
│   ├── components/       # Reusable UI components
│   ├── hooks/            # Custom React hooks
│   └── utils/            # Utility functions
├── vite.config.ts        # Vite configuration
├── tsconfig.app.json     # TypeScript config for app
├── tsconfig.json         # Base TypeScript config
├── .oxlintrc.json        # Oxlint configuration
└── package.json
```

## API Integration

The dashboard communicates with the backend API via REST endpoints. API client configuration is centralized in `src/settings.ts`.

By default, the development proxy routes `/api` requests to `http://localhost:8000`, which is the default port for the [API service](../services/api).

## Testing

Tests are written with Vitest and React Testing Library. Coverage thresholds are enforced at 80% for:
- Lines
- Functions
- Branches
- Statements

Run tests:
```bash
npm run test
```

Run tests with coverage:
```bash
npm run coverage
```

## Linting

The project uses Oxlint for linting with the following plugins:
- React
- TypeScript
- Oxc

Run the linter:
```bash
npm run lint
```

## Type Checking

TypeScript is configured with strict settings. The build script (`npm run build`) runs type checking before creating the production bundle.

## React Compiler

This project uses the [React Compiler](https://react.dev/learn/react-compiler) (enabled via Babel preset) to automatically optimize React re-renders. This may impact Vite dev and build performance slightly.

## Dependencies

### Core
- `react@^19.2.8` - React library
- `react-dom@^19.2.8` - React DOM bindings
- `react-icons@^5.7.0` - Icon library

### Development
- `vite@^8.3.0` - Build tool
- `@vitejs/plugin-react@^6.1.1` - Vite React plugin
- `typescript@~6.0.2` - TypeScript
- `oxlint@^1.81.0` - Linter
- `vitest@^5.0.5` - Test framework

## Related Components

- **[API Service](../services/api)** - Backend REST API (Python/FastAPI)
- **[Android App](../apps/android)** - Steward mobile application (Expo/React Native)

## Repository Context

This component is part of **Case B. Manning/patrol requirement** (formerly Steward Localization), a 5th semester project for BSc Software Engineering at AAU Copenhagen, Autumn 2026.

For more information, see the [main README](../../README.md) and the [semester documentation](https://github.com/aau-cph-sw5/semester-docs).

## License

MIT License - See [LICENSE](../../LICENSE) for details.
