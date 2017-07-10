from enum import auto, Enum
from .connect_source import ConnectSource
from .connect_target import ConnectTarget

class IOModes(Enum):
    PUSH = auto()
    PULL = auto()



class IO:
    pass


class Antenna(IO, ConnectTarget):
    mode = None #must be push or pull

    def push(self, value): #only needs to be defined if mode is "push"
        raise NotImplementedError


class Output(IO, ConnectSource):
    mode = None #must be push or pull

    def pull(self): #only needs to be defined if mode is "pull"
        raise NotImplementedError
