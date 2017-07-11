import hive


def build_decode(i, ex, args):
    """Decode bytes into a string"""
    args.encoding = hive.parameter('str', 'utf-8')
    ex.encoding = hive.attribute('str', args.encoding)

    i.string = hive.attribute("str")
    i.pull_string = hive.pull_out(i.string)
    ex.string = hive.output(i.pull_string)

    i.bytes_ = hive.attribute('bytes')
    i.pull_bytes_ = hive.pull_in(i.bytes_)
    ex.bytes_ = hive.antenna(i.pull_bytes_)

    def do_encoding(self):
        self._string = self._bytes_.decode(self.encoding)

    i.do_encoding = hive.modifier(do_encoding)

    hive.trigger(i.pull_string, i.pull_bytes_, pretrigger=True)
    hive.trigger(i.pull_bytes_, i.do_encoding)


Decode = hive.hive("Decode", build_decode)
