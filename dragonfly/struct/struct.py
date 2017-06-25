import hive
from struct import pack, unpack_from, calcsize, Struct as _Struct


def declare_io(meta_args):
    meta_args.mode = hive.parameter("str", options={'push', 'pull'}, start_value='pull')
    meta_args.method = hive.parameter("method")

def build_io(i, ex, args, meta_args):
    if meta_args.mode == 'pull':
        i.value = hive.attribute()
        i.in_ = hive.pull_in(i.value)
        ex.in_ = hive.antenna(i.in_)

        hive.trigger(i.in_, )

        i.out = meta_args.out(i.value)
        ex.out = hive.output(i.out)
    else:
        i.value = hive.attribute()
        i.in_ = meta_args.in_(i.value)
        ex.in_ = hive.antenna(i.in_)

        i.out = meta_args.out(i.value)
        ex.out = hive.output(i.out)


IOMethod = hive.dyna_hive("IOMethd", build_io, declarator=declare_io)


def build_struct(cls, i, ex, args):
    """Interface to Struct class"""
    i.tuple = hive.attribute("tuple")
    i.pack_in = hive.push_in(i.tuple)
    ex.pack = hive.antenna(i.pack_in)

    i.bytes = hive.attribute("bytes")
    i.unpack_out = hive.push_out(i.bytes)
    ex.unpack = hive.output(i.unpack_out)

    i.size_out = hive.pull_out(cls.size)
    ex.size = hive.output(i.size_out)


class StructCls(_Struct):

    def __init__(cls, fmt: str):
        super().__init__(fmt)


Struct = hive.hive("Struct", build_struct, builder_cls=StructCls)