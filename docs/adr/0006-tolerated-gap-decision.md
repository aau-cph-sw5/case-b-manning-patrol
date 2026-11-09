# ADR POSITIONING INTERFACE CONTRACT.

**Status.** Proposed

**Date.** 2026-10-05

**Deciders.** Team 8, Asbjørn Gosvig, Jakob Michaelsen, Marcus Linde, Nichlas Christiansen, Rohan Atik, Ryan Zachariasen,

**Related backlog items.**  
MET-B-004

Blocks B-005, B-006, B-007

## Context
We assume that a beacon connection is not a connection in the Bluetooth sense. The steward's Android device passively receives advertising packets, and the connection exists for as long as packets keep arriving. Packets are sometimes missed especially when the device is in the pocket of a steward. Without a tolerance, a single stay would split into several shorter records each time the signal dropped, and any piece shorter than x would be discarded, so work actually carried out would go unrecorded.

The gap is therfore bound from two sides:

**Lower bound** The gap must exceed the interruptions that occur while the steward remains in place, so that ordinary packet loss and scan intervals do not split a record.

**Upper bound** The gap must be shorter than the briefest genuine absence we want the system to register. This could be a steward stepping of the train onto the platform, or going up the escalator from the platform to the concourse.

## Decision

> We will treat a beacon as lost only after 10 seconds without an observation. A beacon observed again within 10 seconds continues the open record.

## Consequences
**What becomes easier**
Brief losses of signal no longer fragment records, so a steward who stays in one area produces one record.

**What becomes harder**

An absence of less than 10 seconds is not detected.

An interruption longer than 10 seconds while the steward remains in place still splits the record.

The gap constrains the choice of x. If x is shorter than or equal to the gap, two isolated observations could complete a record consisting mostly of gap time. If x is chosen to be less that the gap, we must choose a new one.

## Alternatives considered
**A tolerated gap of 20 seconds**

This is the current default in the Estimote SDK. It was rejected because it reaches the upper bound, a steward who leaves a stopped train for about 20 seconds to check the platform would not be registered as having left the train.

**A tolerated gap of 5 seconds**

This would register short absences more precisely. It was rejected because it lies close to the interval between observations that Android can produce

## Notes
Industry practice places the value between 10 and 20 seconds:

The Android Beacon Library (AltBeacon) uses a default tolerated gap of 10 seconds https://github.com/AltBeacon/android-beacon-library/blob/aca69f9bc7f3526032e6e5fcc3593a3259c7d2d4/lib/src/main/java/org/altbeacon/beacon/BeaconManager.java#L195-L198

Estimote raised its default from 10 to 20 seconds https://github.com/Estimote/Android-SDK/blob/1f4ef1c1255b2fd4b09c4e80780d342cbb1b09ab/CHANGELOG.md?plain=1#L192-L197

According to estimote 10 seconds can be too short of a gap when scanning is not reliable. We accept that risk because we scan continuously in the foreground and because the upper bound rules out 20 seconds.
