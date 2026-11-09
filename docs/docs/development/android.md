# Android App

Steward-facing Android app built with Expo SDK 57, React Native, and strict TypeScript.

**Location:** `apps/android/`

## Prerequisites

- Node.js 20 or 22
- npm >= 11.4.2
- Expo Go app (for quick testing) or Android emulator

## Running Locally

```bash
cd apps/android
npm install
EXPO_PUBLIC_API_URL=http://<your-lan-ip>:8000 npx expo start
```

From the Expo developer menu, open the app in:
- **Expo Go** (quickest, no build needed)
- **Android emulator**
- **Development build** on a physical device (needed for BLE beacon scanning)

## Commands

| Command | Description |
|---------|-------------|
| `npm run start` | `expo start` |
| `npm run android` | `expo start --android` (emulator) |
| `npm run ios` | `expo start --ios` (simulator) |
| `npm run web` | `expo start --web` |
| `npm run lint` | `expo lint` |
| `npx tsc --noEmit` | TypeScript type check |
| `npm test` | Vitest tests |

## Project Structure

```
apps/android/src/
├── app/                         # expo-router file-based routes
│   ├── index.tsx                # Patrol session slider demo
│   └── beacon.tsx               # Mock beacon scanner demo
├── components/                  # UI building blocks
├── hooks/                       # Connect side effects to state
├── state/                       # Pure reducers
├── types/                       # Domain types and initial states
├── services/                    # External world (beacon scanning)
└── utils/
```

## Beacon Scanning

The app receives beacon connect/disconnect events shaped as `ConnectionEvent`
from `contracts/positioning-ingestion/v2`:

```typescript
{
  android_id: string,
  beacon_id: string,
  event: "connect" | "disconnect",
  timestamp: string
}
```

Everything that produces these events implements the `BeaconScanner` interface
(`src/services/beacon/scanner.ts`).

### Mock vs Real Scanning

- **MockBeaconScanner** — simulates a steward walking past beacon IDs from the
  backend fixtures. No Bluetooth needed; runs in Expo Go and emulator.
- **Real BLE scanning** — same interface, requires a development build on a
  physical device.

!!! warning "Not yet wired up"
    Forwarding events to the backend (`POST /api/v2/connection/connect` and
    `/api/v2/connection/disconnect`) is not implemented yet.

## Conventions

- **Hooks take side effects as parameters** — `usePatrolSession` receives the
  start/stop requests, `useBeaconScanner` receives the scanner. Swap the
  implementation, not the hook.
- **Reducers are pure** — no requests, timers, or other side effects inside.
- **The phone is the source of truth for event time** (see
  [ADR-0004](../adr/0004-positioning-interface-contract.md)).

## Expo Version

!!! info "SDK 57"
    Check the [versioned Expo docs](https://docs.expo.dev/versions/v57.0.0/)
    before writing Expo-specific code. APIs change between versions.
