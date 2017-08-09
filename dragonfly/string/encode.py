import hive


def encode(i, ex):
    i.bytes.value = i.string.value.encode(i.encoding.value)


def build_encode(i, ex, args):
    """Encode a string into bytes"""
    args.encoding = hive.parameter('str', 'utf-8')
    ex.encoding = hive.attribute('str', args.encoding)

    i.string = hive.attribute("str")
    ex.string = i.string.pull_in

    i.bytes = hive.attribute('bytes')
    ex.bytes = i.bytes.pull_out

    i.encode = hive.modifier(encode)
    i.bytes.pull_out.before.connect(i.string.pull_in.trigger)
    i.string.pull_in.after.connect(i.encode.trigger)


Encode = hive.hive("Encode", build_encode)
