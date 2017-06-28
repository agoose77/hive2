class HiveException(Exception):
    pass


class HiveConnectionError(HiveException):
    pass


# Matchmaking
class MatchmakingPolicyError(HiveException):
    pass


# Typing
class TypingError(HiveException):
    pass


class MatchCaseUnhandled(TypingError):
    pass


class MatchFailedError(TypingError):
    pass


class InvalidMatchCase(TypingError):
    pass
