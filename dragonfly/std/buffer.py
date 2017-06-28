import hive


def declare_buffer(meta_args):
    meta_args.data_type = hive.parameter("str", "int")
    meta_args.mode = hive.parameter("str", "push", options={'push', 'pull'})


def build_buffer(i, ex, args, meta_args):
    """Store the input value and output saved value.

    In pull mode, the trigger is used to update the internal value.
    In push mode, the trigger is used to output the internal value.

    Can be used to cache changing values
    """
    args.start_value = hive.parameter(meta_args.data_type, None)
    i.cached_value = hive.attribute(meta_args.data_type, args.start_value)

    def mod(self):
        print("PUSHED")

    i.m = hive.modifier(mod)

    if meta_args.mode == "push":
        i.push_value = hive.push_in(i.cached_value)
        ex.value = hive.antenna(i.push_value)

        i.push_cached_value = hive.push_out(i.cached_value)
        ex.cached_value = hive.output(i.push_cached_value)

        ex.output = hive.entry(i.push_cached_value)
        hive.trigger(i.push_value, i.m)

    elif meta_args.mode == "pull":
        i.pull_value = hive.pull_in(i.cached_value)
        ex.value = hive.antenna(i.pull_value)

        i.pull_cached_value = hive.pull_out(i.cached_value)
        ex.cached_value = hive.output(i.pull_cached_value)

        ex.update_cache = hive.entry(i.pull_value)


Buffer = hive.dyna_hive("Buffer", build_buffer, declarator=declare_buffer)
