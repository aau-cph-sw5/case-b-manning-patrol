from src.models.event import Event
from src.services.coverage.models.presence_interval import PresenceInterval


class IntervalBuilder:
    def build(self, events: list[Event]) -> list[PresenceInterval]:
        """Turn the stored events into presence intervals, one per visit.

        1. Sort the events by device_timestamp (the phone's time), because
           events can arrive out of order.
        2. A CONNECT opens a visit for (actor, beacon). The next DISCONNECT for
           the same pair closes it.
        3. A STOP closes all of that actor's open visits at the STOP time,
           because the phone sends no DISCONNECT when a patrol session stops.
        4. Visits still open at the end keep ended_at = None. Their length is
           measured later against now.
        5. START has no effect here.

        Event.beacon is a string. It is converted to UUID once, and invalid
        values are skipped and logged. No database and no clock, so the same
        events always give the same intervals.
        """
        raise NotImplementedError
