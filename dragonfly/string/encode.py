import hive


def build_encode(i, ex, args):
    """Encode a string into bytes"""
    args.encoding = hive.parameter('str', 'utf-8')
    ex.encoding = hive.attribute('str', args.encoding)

    i.string = hive.attribute("str")
    i.pull_string = hive.pull_in(i.string)
    ex.string = hive.antenna(i.pull_string)

    i.bytes_ = hive.attribute('bytes')
    i.pull_bytes_ = hive.pull_out(i.bytes_)
    ex.bytes_ = hive.output(i.pull_bytes_)

    def do_encoding(self):
        self._bytes_ = self._string.encode(self.encoding)

    i.do_encoding = hive.modifier(do_encoding)

    hive.trigger(i.pull_bytes_, i.pull_string, pretrigger=True)
    hive.trigger(i.pull_string, i.do_encoding)


Encode = hive.hive("Encode", build_encode)
