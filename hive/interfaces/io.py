from enum import auto, Enum

from .connect import ConnectSource, ConnectTarget


class IOModes(Enum):
    PUSH = auto()
    PULL = auto()


class Antenna(ConnectTarget):
    mode = None  # must be push or pull

    def push(self, value):  # only needs to be defined if mode is "push"
        raise NotImplementedError


class Output(ConnectSource):
    mode = None  # must be push or pull

    def pull(self):  # only needs to be defined if mode is "pull"
        raise NotImplementedError
