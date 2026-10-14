# Manning Patrol Android Frontend

Steward-facing Android app for the Manning Patrol system: shows and drives the steward's
patrol session, and receives the beacon signals that document presence. Built with Expo SDK 57,
React Native, expo-router and strict TypeScript.

## Setup

```bash
npm install
npx expo start
```

From the Expo developer menu, open the app in Expo Go, on an Android emulator, on the iOS
simulator, or in a development build. Some hardware-dependent features (see Beacon
scanning below) need a development build on a physical device.

## Commands

```bash
npm run start     # expo start
npm run android    # expo start --android (emulator)
npm run ios        # expo start --ios (simulator)
npm run web        # expo start --web
npm run lint       # expo lint
npx tsc --noEmit   # typecheck, what CI effectively checks (no test suite yet)
```

## Project structure

```
src/
├── app/        expo-router file-based routes
│   ├── index.tsx   patrol session slider demo 
│   └── beacon.tsx  mock beacon scanner demo
├── components/ ui building blocks
├── hooks/      connect side effects to state 
├── state/      pure reducers
├── types/      domain types and initial states
├── services/   the outside world: beacon scanning lives here
└── utils/
```

## Beacon scanning

The app receives beacon connect/disconnect events shaped as `ConnectionEvent` from
`contracts/positioning-ingestion/v2` (`android_id`, `beacon_id`, `event`, `timestamp`).
Everything that produces these events implements the `BeaconScanner` interface
(`src/services/beacon/scanner.ts`).

Until real BLE scanning lands, `MockBeaconScanner` simulates a steward walking past the
beacon ids from the backend fixtures: connect, hold, disconnect, next beacon. It involves
no Bluetooth, so it runs in Expo Go and on the emulator. Real BLE scanning is the same
interface on a development build on a physical device.

Forwarding the events to the backend (`POST /api/v2/connection/connect` and
`/api/v2/connection/disconnect`) is not wired up yet.

## Conventions

- Hooks take their side effects as parameters: `usePatrolSession` receives the start/stop
  requests, `useBeaconScanner` receives the scanner. Swap the implementation, not the hook.
- Reducers are pure; no requests, timers or other side effects inside.
- The phone is the source of truth for event time (ADR-0004).
- Check the versioned Expo docs before writing Expo-specific code (see AGENTS.md).
