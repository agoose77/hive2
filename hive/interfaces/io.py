from enum import auto, Enum


class IOModes(Enum):
    PUSH = auto()
    PULL = auto()



class IO:
    pass


class Antenna(IO):
    mode = None #must be push or pull

    def push(self, value): #only needs to be defined if mode is "push"
        raise NotImplementedError


class Output(IO):
    mode = None #must be push or pull

    def pull(self): #only needs to be defined if mode is "pull"
        raise NotImplementedError
