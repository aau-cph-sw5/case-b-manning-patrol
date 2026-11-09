# ADR 0012. Train manning gets its own server-sent events stream.

**Status.** Proposed
**Date.** 2026-11-05
**Deciders.** Asbjørn Gosvig, Jakob Michaelsen, Marcus Linde, Nichlas Christiansen, Rohan Atik, Ryan Zachariasen, team 8
**Related backlog items.** MET-B-011, MET-B-012
**Supersedes.** [ADR 0011](00011-server-sent-events.md)

## Context

ADR 0011 chose server-sent events (SSE) for live updates and said that the web dashboard and the Android steward app would listen to the same stream. At the time, that stream only carried stations, which both apps need: the dashboard shows patrol compliance, and the stewards see which levels are due.

MET-B-011 adds train manning: how much of the trains' running time has been manned so far tonight, for the whole fleet and for the M1/M2 and M3/M4 line groups. Only the control room needs this. The steward app has no screen that uses it.

The first version (PR #175) put the trains into the shared dashboard event. Each train carried its total and manned time in seconds, and the web dashboard worked out the counts and percentages itself. That meant the Android app received the whole fleet on every update only to throw it away, and every change to the train data became a change to the stream the steward app depends on.

The team tried a separate stream (PR #186), briefly went back to the shared event, and settled on the split the same day (PR #187). Shortly after, the calculation moved to the backend and the per-train seconds were removed from the contract (PR #195).

## Decision

Server-sent events stay, as decided in ADR 0011. What changes is how the data is divided:

- `/api/v2/dashboard/stream` carries stations only and is used by both the web dashboard and the Android app.
- `/api/v2/trains/stream` carries train manning and is used by the web dashboard only.

The backend calculates the manning percentages (overall, M1/M2 and M3/M4) and sends them ready to display, together with which stewards are on each train right now. As on the station stream, every message holds the full current picture, and a client that connects gets the latest one straight away.

## Consequences

Positive impact

- The steward app only receives what it shows. It no longer downloads the whole fleet every few seconds just to ignore it.
- Train manning can change without touching the contract the Android app is built against. When the percentages changed from ratios to 0–100 (PR #200), the station stream was not affected.
- The compliance figure is worked out in one place. The dashboard shows the number the backend calculated, and a later report can reuse the same calculation instead of repeating it. This follows ADR 0004, which keeps business logic out of the dashboard.

Potential drawbacks

- The web dashboard keeps two connections open instead of one and has to recover each of them if it drops.
- The backend now has two nearly identical sets of stream code (endpoint, broadcaster and clock tick). A fix in one has to be remembered in the other.
- The operator can no longer see how the figure was built. Without per-train manned and running time, the dashboard cannot show which trains pulled the percentage down.
- The move to the backend is not complete. The 70 percent target and the pass/fail comparison still live in the web client (`TrainCard.tsx`).
- Undoing the split later would mean changing the contract and both clients.

## Alternatives considered

**Keep trains in the shared dashboard event.** This was built and merged first (PR #175). Rejected because the steward app would keep receiving train data it never uses, and every change to train manning would ride on the stream the Android app depends on.

**One stream with a filter.** Each client could ask for the parts it wants, for example `?include=trains`. That keeps a single connection per client, but the same endpoint would return different shapes depending on who asks, which is harder to describe in the contract and to test. This option was not discussed at the time.

**Let the web dashboard calculate the percentages** from per-train manned and running time, as in PR #175. Rejected because the compliance rule would then live in the frontend, and a report or another client would have to repeat it. The per-train times were also judged unnecessary for the product (PR #194).

## Notes

- This ADR supersedes ADR 0011. The only part of 0011 that no longer holds is "Both the web dashboard and the Android steward app consume the same stream." The choice of SSE, and the reasons it was preferred over WebSockets and polling, still stand and are kept in ADR 0011.
- The written reason for the split is that the Android app should only receive stations (PRs #186 and #187). Why #186 was first withdrawn and then redone in #187 is not written down.
- The contract change is described in `contracts/api/v2/positioning-interface/` (see `CHANGELOG.md`, v2.4.0 and v2.5.0).
