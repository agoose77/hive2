import hive


def decode(i, ex):
    i.string.value = i.bytes.value.decode(i.encoding.value)


def build_decode(i, ex, args):
    """Decode bytes into a string"""
    args.encoding = hive.parameter('str', 'utf-8')
    i.encoding = hive.attribute('str', args.encoding)
    ex.encoding = i.encoding.property()

    i.string = hive.attribute("str")
    ex.string = i.string.pull_out

    i.bytes = hive.attribute('bytes')
    ex.bytes = i.bytes.pull_in

    i.decode = hive.modifier(decode)
    i.string.pull_out.before.connect(i.bytes.pull_in.trigger)
    i.bytes.pull_in.after.connect(i.decode.trigger)


Decode = hive.hive("Decode", build_decode)
