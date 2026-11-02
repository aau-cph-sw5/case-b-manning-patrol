# ADR 0011. Server-sent events for live compliance updates and steward alerts.

**Status.** Proposed
**Date.** 2026-10-19
**Deciders.** Asbjørn Gosvig, Jakob Michaelsen, Marcus Linde, Nichlas Christiansen, Rohan Atik, Ryan Zachariasen, team 8
**Related backlog items.** MET-B-007, MET-B-008, MET-B-009, MET-B-012, MET-B-013, MET-B-014, MET-B-015, MET-B-024

## Context

Two clients need server-initiated updates. The web dashboard must show the current compliance status (trains manned >= 70% of running time and every station level patrolled hourly) without operations staff manually refreshing. The Android steward app must receive alerts and other relevant information — for example emerging compliance gaps or changes affecting their shift — pushed to them as they happen. In both cases the compliance state changes on the server side, when positioning and patrol events arrive in the event store, and the clients are pure consumers of that state: they never send data back on the same channel.

The backend is FastAPI, which supports streaming responses (`text/event-stream`) natively, and both clients — the browser-based dashboard and the Expo / React Native steward app — can consume an SSE stream. The traffic is one-way, server-to-client, over plain HTTP.

## Decision

We will push live compliance updates and steward alerts from the API using Server-Sent Events (SSE): a long-lived HTTP response of type `text/event-stream`. Both the web dashboard and the Android steward app consume the same stream.

## Consequences

Positive impact

SSE matches the actual communication pattern: the server talks, clients listen. One mechanism serves both the dashboard and the steward app, instead of maintaining two push paths. It is plain HTTP, so it needs no protocol upgrade, works through existing proxies and load balancers, and is compatible with the API's ordinary authentication. Browser `EventSource` reconnects automatically after dropped connections, and the implementation surface is much smaller than a bidirectional protocol would be.

Potential drawbacks

On Android, mobile networks drop long-lived connections far more often than fixed lines, so the steward app must tolerate reconnect cycles and catch up on anything missed rather than silently losing alerts. The stream only works while the app is in the foreground, which is acceptable while a steward is on duty, but it is not a substitute for OS-level push if alerts must reach a closed app.

## Alternatives considered

**WebSockets.** Full-duplex and lower overhead per message, but both clients only consume updates, so bidirectionality buys nothing here. WebSockets add an upgrade handshake, a separate framing protocol, manual reconnection and heartbeat logic, and more connection state on the server. For a one-way push, that is complexity without benefit.

**Client-side polling.** The simplest option, but it forces a trade-off between latency and load: polling often enough for near-real-time compliance status and alerts means a stream of mostly wasted requests when nothing has changed, while SSE pushes exactly when the server state changes. No polling was also an acceptance criterion in MET-B-0002.

## Notes
