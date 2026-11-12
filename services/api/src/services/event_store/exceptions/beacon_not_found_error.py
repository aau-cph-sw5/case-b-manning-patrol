"""Error raised when an event refers to an unknown beacon."""


class BeaconNotFoundError(Exception):
    """An event refers to a beacon that is not known."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
