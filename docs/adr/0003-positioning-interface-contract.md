# ADR POSITIONING INTERFACE CONTRACT.

**Status.** Proposed | Accepted | Superseded by ADR {NNNN} | Deprecated

**Date.** 2026-9-23

**Deciders.** Team 8, Jakob Michaelsen, Nichlas Christiansen, Marcus Linde, Ryan Zachariasen, Asbjørn Gosvig

**Related backlog items.** MET-B-002

## Context
The PBI gave us some boundaries described in the acceptance criteria, were it demanded that we created an observation based design, where we dont poll constantly for updates. Furthermore, we have to manage connectivity so the server and the dashboard client knows when android client is connected. This incentives us have to manage which component will be "source of truth" regarding timestamps beacon connectivity.
## Decision
> The android client will send connection events to the server, which will propagate scenario state to connected clients via a WebSocket connection. We will use the server as a source of truth regarding timestamps and beacon connectivity.
## Consequences
WebSockets introduces a layer of complexity and security measures in the implementation, but it reduces the network traffic, as we dont have to poll constantly for data via. HTTP, as the acceptance criteria demanded.

When we use the server as a source of truth, we have to rely on regular connection from the android client, which might not be guaranteed by the environment of the Metro stations or tunnels. E.g, if the client does not have connection to the server, it can not tell the server, if it's left a station, and the servers "truth" will be false. This might require workarounds where we handle the offline state, trying to reconnect.
## Alternatives considered
**{Alternative}.** Why it was rejected, specifically. "Too complex" is not a
reason; "it would require every client to hold an open connection through a tunnel
where the network drops for minutes at a time" is.

**{Alternative}.** As above.

## Notes

Anything a successor would want: a link to the discussion, the measurement that
settled it, the Metro answer that constrained it, the date it should be revisited.
