# ADR POSITIONING INTERFACE CONTRACT.

**Status.** Proposed

**Date.** 2026-9-23

**Deciders.** Team 8, Asbjørn Gosvig, Jakob Michaelsen, Marcus Linde, Nichlas Christiansen, Rohan Atik, Ryan Zachariasen,

**Related backlog items.**  
B-002

Blocks: B-003, B-004, B-006, B-007, B-012, B-014, B-025

## Context
The PBI demanded in the acceptance criteria that we create an observation-based design, where we don't poll constantly for updates. Furthermore, we have to manage connectivity so the server and the dashboard client know when the Android client is connected. This incentivizes us to manage which component will be the "source of truth" regarding timestamps and beacon connectivity. We also know that one station can have multiple beacons, e.g., Marmorkirken and Kongens Nytorv station have two beacons, both on separate platforms, and eventually all stations will have beacons on the concourse

## Decision

> The model is not divided into stations and trains, but areas defined by beacons: train, concourse, and platform.

> The Android client will send connection events to the server, which will propagate scenario state to connected clients via a WebSocket connection.

> The Android client will send connection events as the source of origin to the server.

> The backend will be the source of truth for data propagated to the dashboard.

## Consequences
When we model the locations after beacons, it makes it easier to know exactly where the stewards are. The downside to this approach is it introduces a more complex database schema.

WebSockets introduce a layer of complexity and security measures in the implementation, but they reduce the network traffic, as we don't have to poll constantly for data via HTTP, as the acceptance criteria demanded.

Using the Android client as a source of origin for time gives the ability to have better timekeeping due to not being dependent on a constant connection to the backend for reliable data transfers. The drawback is the potential for time manipulation by the user of the Android device.

When we use the server as a source of truth, we avoid doing business logic in the dashboard's frontend. If the Android device disconnects, the backend may continue exposing the last known value unless the system handles stale data.

## Alternatives considered
**Using client as source of truth.** We considered the server keeping track of time due to the potential of the user manipulating data, but due to the acceptance criteria and the lack of reliability on connection in the metro system, we opted not to.

## Notes
We assume that the stewards will have a working phone, and that it will not run out of power. 
An open question is we do not know the procudere of ownership for the andriod devices.
