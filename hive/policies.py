"""Plugin donation policies.

Defines policies for plugin donation
"""

from abc import ABC, abstractproperty
from collections import namedtuple

from .exception import MatchmakingPolicyError

ConnectionLimits = namedtuple("ConnectionLimits", "min max")


class MatchmakingPolicy(ABC):
    limits: ConnectionLimits = abstractproperty()

    def __init__(self):
        self._connections = 0

    def on_connected(self):
        self._connections += 1

    @property
    def is_valid(self) -> bool:
        lower, upper = self.limits
        count = self._connections

        valid = True

        if lower is not None:
            valid = count >= lower

        if upper is not None:
            valid = valid and count <= upper

        return valid

    def pre_connected(self):
        if self._connections == self.limits.max:
            raise MatchmakingPolicyError("Policy {!r} forbids further connections".format(self.__class__.__name__))

    def validate(self):
        if not self.is_valid:
            raise MatchmakingPolicyError("Policy {!r} was not satisfied".format(self.__class__.__name__))


class SingleRequired(MatchmakingPolicy):
    """One connection only must be established"""

    limits = ConnectionLimits(1, 1)


class SingleOptional(MatchmakingPolicy):
    """At most, one connection can be established"""

    limits = ConnectionLimits(None, 1)


class MultipleRequired(MatchmakingPolicy):
    """One or more connections must be established"""

    limits = ConnectionLimits(1, None)


class MultipleOptional(MatchmakingPolicy):
    """Any number of connections can be established"""

    limits = ConnectionLimits(None, None)
