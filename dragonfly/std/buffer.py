import hive


def configure_buffer(meta_args):
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

    if meta_args.mode == "push":
        ex.value = i.cached_value.push_in
        ex.cached_value = i.cached_value.push_out
        ex.push_out = i.cached_value.push_out.trigger

    elif meta_args.mode == "pull":
        ex.value = i.cached_value.pull_in
        ex.cached_value = i.cached_value.pull_out
        ex.pull_in = i.cached_value.pull_out.trigger


Buffer = hive.dyna_hive("Buffer", build_buffer, configurer=configure_buffer)
