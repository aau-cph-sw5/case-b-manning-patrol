"""Replay the fixture event timeline against a running dev server.

Sends every entry of fixtures/fixture-events-v1.json to the v2 ingestion
endpoints of `uv run dev`, wrapped in a patrol-session start/stop like the
seed script, so each fake event passes the mock-token authentication and the
RBAC check in src/authorization. Exits non-zero if any event is rejected.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

FIXTURE_PATH = Path(__file__).parents[2] / "fixtures" / "fixture-events-v1.json"

EVENT_ROUTES = {
    "CONNECTED": "/connection/connect",
    "DISCONNECTED": "/connection/disconnect",
}


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _post(base_url: str, token: str, route: str, payload: dict) -> int:
    request = urllib.request.Request(
        base_url + route,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code


def build_timeline(fixture: list[dict]) -> list[tuple[str, str, datetime, str | None]]:
    """Wrap the fixture events in a patrol-session start and stop."""
    first = _parse_timestamp(fixture[0]["timestamp"])
    last = _parse_timestamp(fixture[-1]["timestamp"])
    timeline = [
        (
            entry["event"],
            EVENT_ROUTES[entry["event"]],
            _parse_timestamp(entry["timestamp"]),
            entry["beacon_id"],
        )
        for entry in fixture
    ]
    timeline.append(
        ("start", "/patrol-session/start", first - timedelta(minutes=1), None)
    )
    timeline.append(("stop", "/patrol-session/stop", last + timedelta(minutes=1), None))
    return sorted(timeline, key=lambda item: item[2])


def main() -> None:
    """POST the fixture timeline to the dev server and report rejections."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=os.environ.get("API_BASE_URL", "http://localhost:8000/api/v2"),
    )
    parser.add_argument(
        "--token", default=os.environ.get("DEV_TOKEN", "dev-steward-token")
    )
    parser.add_argument(
        "--speed", type=float, default=100, help="playback speed multiplier"
    )
    args = parser.parse_args()

    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    android_id = fixture[0]["android_id"]
    failures = 0
    previous: datetime | None = None
    for name, route, timestamp, beacon_id in build_timeline(fixture):
        if previous is not None:
            delay = (timestamp - previous).total_seconds() / args.speed
            if delay > 0:
                time.sleep(delay)
        previous = timestamp
        payload: dict = {"android_id": android_id, "timestamp": timestamp.isoformat()}
        if beacon_id is not None:
            payload["beacon_id"] = beacon_id
        status = _post(args.base_url, args.token, route, payload)
        print(f"{'ok' if status == 201 else 'REJECTED'} {status} {name} {route}")
        if status != 201:
            failures += 1
    if failures:
        sys.exit(f"{failures} fixture events were rejected")
    print(f"Replayed the fixture timeline to {args.base_url} as {args.token}")


if __name__ == "__main__":
    main()
