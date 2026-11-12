"""Error raised when the device that sent an event is unknown."""


class AndroidIdNotFoundError(Exception):
    """The device that sent an event is not known."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
