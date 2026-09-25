# Fixtures

## Files

| File | Contents |
|------|----------|
| `fixture-events-v1.json` | Merged event timeline for steward 1: one entry per event with `debugging_number`, `event` (`CONNECTED`/`DISCONNECTED`), `android_id`, `beacon_id`, `timestamp`. |

## Beacon naming

For simplification, beacon IDs `50` and over are trains; everything below is a station.

| Beacon ID suffix | Area |
|------------------|------|
| `...0002` | Station 2 |
| `...0003` | Station 3 |
| `...0004` | Station 4 |
| `...0050` | Train 50 |
| `...0060` | Train 60 |

## What the fixture covers

Every event carries a `debugging_number` (1-16) in chronological order. The
fixture deliberately covers three scenarios:

### 1. A gap exceeding the hourly patrol requirement — events 7 and 15

Steward 1 disconnects from station 3 at 03:10:27 (event **7**) while riding
train 50, and does not return to station 3 until 04:45:40 (event **15**),
when arriving on train 60. Station 3 is therefore unmanned for about 95
minutes — well over the hourly patrol requirement.

(The break between events **12** and **13** is a second long gap: the
steward disconnects from station 4 at 03:20:46 and reconnects at 04:25:59,
about 65 minutes later.)

### 2. Two areas observed at once — events 2-9 and events 14-16

A steward riding a train is simultaneously connected to the train beacon
and to station beacons as the train passes through:

- While on train 50 (connected at event **2**, 03:08:50), the steward is
  also connected to station 2 (events **3-5**), station 3 (events **6-7**),
  and station 4 (event **8**) before stepping off the train (event **9**,
  03:11:15).
- The same happens on train 60: connected at event **14** (04:35:40),
  station 3 connects at event **15** (04:45:40), and train 60 only
  disconnects at event **16** (04:50:40).

Any logic that assumes one active area at a time must handle these
overlapping intervals.

### 3. A connection that drops and returns within a few seconds (< 8 seconds)

Two brief signal losses exist in the fixture:

- Station 2: disconnects at 03:09:20 (event **3**), reconnects at 03:09:24
  (event **4**) — 4 seconds.
- Station 4: disconnects at 03:12:00 (event **10**), reconnects at 03:12:07
  (event **11**) — 7 seconds. The steward has not moved; this is a signal
  blip, not a departure.

A drop-and-return of less than 8 seconds should be treated as the steward
never having left the area.

## Storyline

1. Steward 1 connects to station 2, then boards train 50, riding it through
   station 3 to station 4, and steps off the train.
2. The connection to station 4 blips out and returns within a few seconds.
3. Steward 1 takes a break, disconnecting from station 4 and returning
   roughly an hour later.
4. Steward 1 boards train 60 to station 3, leaving station 3 unmanned for
   over an hour in the meantime.

## Full event list

All timestamps are 2026-05-30 (UTC), android device
`660e8400-e29b-41d4-a716-446655440001`.

| # | Event | Area | Timestamp |
|---|-------------|----------|-----------|
| 1 | CONNECTED | Station 2 | 03:08:13 |
| 2 | CONNECTED | Train 50 | 03:08:50 |
| 3 | DISCONNECTED | Station 2 | 03:09:20 |
| 4 | CONNECTED | Station 2 | 03:09:24 |
| 5 | DISCONNECTED | Station 2 | 03:09:46 |
| 6 | CONNECTED | Station 3 | 03:10:13 |
| 7 | DISCONNECTED | Station 3 | 03:10:27 |
| 8 | CONNECTED | Station 4 | 03:11:00 |
| 9 | DISCONNECTED | Train 50 | 03:11:15 |
| 10 | DISCONNECTED | Station 4 | 03:12:00 |
| 11 | CONNECTED | Station 4 | 03:12:07 |
| 12 | DISCONNECTED | Station 4 | 03:20:46 |
| 13 | CONNECTED | Station 4 | 04:25:59 |
| 14 | CONNECTED | Train 60 | 04:35:40 |
| 15 | CONNECTED | Station 3 | 04:45:40 |
| 16 | DISCONNECTED | Train 60 | 04:50:40 |
