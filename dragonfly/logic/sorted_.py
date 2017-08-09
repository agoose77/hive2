import hive


def configure_sorted(meta_args):
    meta_args.data_type = hive.parameter('str', 'list', {'list', 'dict', 'set', 'tuple'})


def sort(i, ex):
    i.result.value = sorted(i.value.value, reverse=i.reverse.value)


def build_sorted(i, ex, args, meta_args):
    """Sort an iterable and output list"""
    args.reverse = hive.parameter('bool', False)
    i.reverse = hive.attribute('bool', args.reverse)

    i.result = hive.attribute('list')
    ex.result = i.result.pull_out

    i.value = hive.attribute(meta_args.data_type)
    ex.value = i.value.pull_in

    i.sort = hive.modifier(sort)
    i.result.pull_out.before.connects(i.value.pull_in.trigger,
                                          i.sort.trigger)


Sorted = hive.dyna_hive("Sorted", build_sorted, configure_sorted)
