# Manning Patrol – Android frontend

The steward's app. Built with Expo SDK 57 (Expo Router, React Native 0.86, TypeScript in strict mode).
Expo changes quickly, so check the [SDK 57 docs](https://docs.expo.dev/versions/v57.0.0/) rather than older tutorials.

## Run it

```bash
npm install
npx expo start      # scan the QR code with Expo Go, or press "a" for an Android emulator
npx tsc --noEmit    # type-check
```

`npm run lint` sets up ESLint the first time it runs, which edits `package.json`. Agree on it as a team before committing that.

## Folder layout

| Folder | Contains |
|---|---|
| `src/app/` | Routes only, plus `_layout.tsx`. Every file here becomes a screen, so put nothing else here. |
| `src/components/` | UI components |
| `src/hooks/` | Custom hooks |
| `src/state/` | Pure state logic (reducers) |
| `src/types/` | Shared types |
| `src/utils/` | Pure helper functions |

Use named exports outside `src/app/` (routes use `export default`), and import with the `@/` alias (`@/components/...`) instead of `../`.

## Session button

The steward starts and stops a **session** (e.g. around a break) with one button at the bottom of the home screen.

| Status | Button |
|---|---|
| `stopped` | green, play icon, "Start" |
| `starting` | grey, spinner, "Starting...", can't be pressed |
| `active` | red, stop icon, "Stop", live timer `HH:MM:SS` |
| `stopping` | grey, spinner, "Stopping...", can't be pressed |

A failed request puts the button back in the status that is still true and shows the error under it.

| File | Job |
|---|---|
| `src/components/SessionButton.tsx` | The button. UI only: shows the session state it's given and calls `onPress`. |
| `src/hooks/useSession.ts` | Connects the button to the reducer and to the start/stop requests it is given. |
| `src/state/sessionReducer.ts` | Decides the next status. The transition table is at the top of the file. |
| `src/types/session.ts` | `SessionStatus`, `SessionState`, `SessionAction` |

### Connecting the API

**Not connected yet.** `src/app/index.tsx` shows the button in its starting state with an empty `onPress`, because the session API is a separate ticket. Connecting it takes two steps:

**1. Write the requests**, e.g. in `src/api/session.ts`: two functions that send `POST /api/v1/session/start` and `/stop`. Each must return a `Promise<void>` that **resolves when the server answers 201 and rejects otherwise**. That is all `useSession` relies on. Put the server address in `EXPO_PUBLIC_API_URL` in `.env.local` (gitignored).

**2. Replace the placeholder in `src/app/index.tsx`:**

```tsx
const { state, toggle } = useSession({ start: startSession, stop: stopSession });

<SessionButton {...state} onPress={toggle} />
```

`useSession` handles the rest: the status changes, the error text, and ignoring extra taps while a request is in flight. The timer starts at `00:00:00` when the start is confirmed. The steward sees `useSession`'s own error text, because the API's error `message` is meant for developers.
