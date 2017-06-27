import hive
from enum import IntEnum, auto


_colours = [
    (255, 255, 95),
    (255, 0, 0),
    (0, 255, 0),
    (204, 255, 102),
    (55, 55, 255),
    (5, 207, 146),
    (255, 160, 130),
    (0, 120, 155),
    (0, 120, 155),
    (88, 228, 255),
    (255, 255, 255),
]


_base_type_colours = {
    "entity": _colours[0],
    "trigger": _colours[1],
    "id": _colours[2],
    "str": _colours[3],
    "bytes": _colours[3],
    "int": _colours[4],
    "float": _colours[5],
    "bool": _colours[6],
    "vector": _colours[7],
    "matrix": _colours[8],
    "colour": _colours[9]
}


def get_colour(data_type):
    """Return the appropriate socket colour for data type"""
    base_type = hive.get_base_data_type(data_type)

    try:
        return _base_type_colours[base_type]
    except KeyError:
        pass


    return _colours[10]


class SocketTypes(IntEnum):
    circle = auto()
    square = auto()
    diamond = auto()


_mode_shapes = {
    "pull": SocketTypes.square,
    "push": SocketTypes.circle,
    "any": SocketTypes.square
}


def get_shape(mode):
    try:
        return _mode_shapes[mode]
    except KeyError:
        raise ValueError("Invalid mode")

