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
| `src/components/SessionButton.tsx` | The button. UI only: shows the status it's given and calls `onPress`. |
| `src/state/sessionReducer.ts` | Decides the next status. The transition table is at the top of the file. |
| `src/types/session.ts` | `SessionStatus`, `SessionState`, `SessionAction` |

**Not connected yet.** `src/app/index.tsx` shows the button in the `stopped` state with an empty `onPress`. Connecting it to the reducer and the session API belongs to a separate ticket. It looks like this:

```tsx
const [session, dispatch] = useReducer(sessionReducer, initialSessionState);

async function start() {
  dispatch({ type: "START_REQUESTED" });
  try {
    await postSessionStart(); // the real api call
    dispatch({ type: "START_SUCCEEDED", startedAt: Date.now() });
  } catch {
    dispatch({ type: "START_FAILED", error: "Could not start the session. Try again." });
  }
}
// stop works the same way with STOP_REQUESTED / STOP_SUCCEEDED / STOP_FAILED

<SessionButton
  status={session.status}
  startedAt={session.startedAt}
  error={session.error}
  onPress={session.status === "stopped" ? start : stop}
/>
```

`startedAt` is taken when the start is confirmed, so the timer starts at `00:00:00`. Show your own error text: the API's error `message` is meant for developers.
