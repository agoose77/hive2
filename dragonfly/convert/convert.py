from collections import OrderedDict

import hive


_type_map = OrderedDict((("str", str), ("bool", bool), ("int", int), ("float", float), ("dict", dict), ("list", list),
                         ("set", set), ("tuple", tuple), ("bytes", bytes)))


def declare_convert(meta_args):
    meta_args.from_data_type = hive.parameter("str", "int")
    meta_args.to_data_type = hive.parameter("str", "int")
    meta_args.mode = hive.parameter("str", "pull", {"push", "pull"})
    meta_args.conversion = hive.parameter("str", "duck", {"duck", "cast"})


def move_value(self):
    self._value_out = self._value_in


def build_convert(i, ex, args, meta_args):
    i.value_in = hive.variable(meta_args.from_data_type)
    i.value_out = hive.variable(meta_args.to_data_type)

    # For push in, push out
    if meta_args.mode == "push":
        i.ppin = hive.push_in(i.value_in)
        i.ppout = hive.push_out(i.value_out)

        hive.trigger(i.ppin, i.ppout)

    else:
        i.ppin = hive.pull_in(i.value_in)
        i.ppout = hive.pull_out(i.value_out)

        hive.trigger(i.ppout, i.ppin, pretrigger=True)

    ex.value_in = hive.antenna(i.ppin)
    ex.value_out = hive.output(i.ppout)

    # For casting (explicit conversion)
    if meta_args.conversion == "cast":
        to_base_type_name = hive.get_base_data_type(meta_args.to_data_type)
        value_cls = _type_map[to_base_type_name]

        def converter(self):
            self._value_out = value_cls(self._value_in)

        i.do_conversion = hive.modifier(converter)
        hive.trigger(i.ppout, i.do_conversion, pretrigger=True)

    # For duck typing, move value through
    else:
        i.move_value = hive.modifier(move_value)
        hive.trigger(i.ppin, i.move_value)


Convert = hive.dyna_hive("Convert", builder=build_convert, declarator=declare_convert)
