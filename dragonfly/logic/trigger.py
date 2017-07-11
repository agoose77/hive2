import hive
import string


def declare_trigger(meta_args):
    meta_args.count = hive.parameter("int", 1, options={x + 1 for x in range(26)})


def build_trigger(i, ex, args, meta_args):
    """Collapse multiple trigger inputs to single trigger output"""
    i.trigger = hive.triggerfunc()

    ex.trigger = i.trigger.triggered

    for index, char in zip(range(meta_args.count), string.ascii_lowercase):
        setattr(ex, char, i.trigger.trigger)


Trigger = hive.dyna_hive("Trigger", build_trigger, declare_trigger)
