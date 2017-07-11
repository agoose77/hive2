from collections import OrderedDict

import hive


_type_map = OrderedDict((("str", str), ("bool", bool), ("int", int), ("float", float), ("dict", dict), ("list", list),
                         ("set", set), ("tuple", tuple), ("bytes", bytes)))


def declare_convert(meta_args):
    meta_args.from_data_type = hive.parameter("str", "int")
    meta_args.to_data_type = hive.parameter("str", "int")
    meta_args.mode = hive.parameter("str", "pull", {"push", "pull"})
    meta_args.conversion = hive.parameter("str", "duck", {"duck", "cast"})


def move_value(i, ex):
    i.converted.value = i.value.value


def build_convert(i, ex, args, meta_args):
    i.value = hive.attribute(meta_args.from_data_type)
    if meta_args.conversion == "duck":
        i.converted = i.value
    else:
        i.converted = hive.attribute(meta_args.to_data_type)

    # For push in, push out
    if meta_args.mode == "push":
        i.value_in = i.value.push_in
        i.converted_out = i.converted.push_out
        i.value_in.triggered.connect(i.converted_out.trigger)

    else:
        i.value_in = i.value.pull_in
        i.converted_out = i.converted.pull_out
        i.converted_out.pre_triggered.connect(i.value_in.trigger)

    ex.value = i.value_in
    ex.converted = i.converted_out

    # For casting (explicit conversion)
    if meta_args.conversion == "cast":
        to_base_type_name = hive.get_base_data_type(meta_args.to_data_type)
        value_cls = _type_map[to_base_type_name]

        def converter(i, ex):
            i.converted.value = value_cls(i.value.value)

        i.do_conversion = hive.modifier(converter)
        i.converted_out.pre_triggered.connect(i.do_conversion.trigger)


Convert = hive.dyna_hive("Convert", builder=build_convert, declarator=declare_convert)
