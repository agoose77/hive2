import hive


class DictCls:

    def __init__(self):
        self.dict = None
        self.key = None
        self.value = None
        self._hive = hive.get_run_hive()

    def set_value(self):
        self.dict[self.key] = self.value

    def get_value(self):
        self.value = self.dict[self.key]


def configure_dictionary(meta_args):
    meta_args.key_data_type = hive.parameter('str', "str.id")
    meta_args.data_type = hive.parameter("str", "int")


def build_dictionary(i, ex, args, meta_args):
    """Interface to dictionary object"""
    ex.dict = hive.property(cls, "dict", "dict")

    i.dict_in = hive.push_in(ex.dict)
    ex.dict_ = hive.antenna(i.dict_in)

    i.dict_out = hive.pull_out(ex.dict)
    ex.dict_out = hive.output(i.dict_out)

    i.key = hive.property(cls, "key", meta_args.key_data_type)
    i.value = hive.property(cls, "value", meta_args.data_type)

    # Setitem
    i.set_key_in = hive.pull_in(i.key)
    ex.set_key = hive.antenna(i.set_key_in)

    i.in_value = hive.push_in(i.value)
    ex.in_value = hive.antenna(i.in_value)

    i.set_value = hive.triggerable(cls.set_value)

    hive.trigger(i.in_value, i.set_key_in)
    hive.trigger(i.set_key_in, i.set_value)

    i.get_key_in = hive.pull_in(i.key)
    ex.get_key = hive.antenna(i.get_key_in)

    i.out_value = hive.pull_out(i.value)
    ex.out_value = hive.output(i.out_value)

    i.get_value = hive.triggerable(cls.get_value)

    # Before outputting, update key
    hive.trigger(i.out_value, i.get_key_in, pretrigger=True)
    hive.trigger(i.get_key_in, i.get_value)


Dictionary = hive.dyna_hive("Dictionary", build_dictionary, configure_dictionary, DictCls)