"""Validation error raised when an event or adjustment is invalid."""


class EventValidationError(Exception):
    """An event or adjustment is invalid; the API answers 400."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
