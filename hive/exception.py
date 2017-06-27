class HiveException(Exception):
    pass


class HiveConnectionError(HiveException):
    pass


class TypingError(HiveException):
    pass


class MatchCaseUnhandled(TypingError):
    pass


class MatchFailedError(TypingError):
    pass


class InvalidMatchCase(TypingError):
    pass

