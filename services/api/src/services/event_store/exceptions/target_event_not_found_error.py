"""Error raised when an adjustment targets a missing event."""


class TargetEventNotFoundError(Exception):
    """An adjustment targets an event that does not exist; the API answers 404."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
