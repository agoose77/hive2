import hive


def build_conjugate(i, ex, args):
    """Calculate the complex conjugate of a complex number"""
    i.value = hive.attribute('complex')
    i.conjugate = hive.attribute('complex')

    i.pull_conjugate = hive.pull_out(i.conjugate)
    ex.conjugate = hive.output(i.pull_conjugate)

    i.pull_value = hive.pull_in(i.value)
    ex.value = hive.antenna(i.pull_value)

    def build_conjugate(self):
        self._conjugate = self._value.conjugate()

    i.build_conjugate = hive.modifier(build_conjugate)

    hive.trigger(i.pull_conjugate, i.pull_value, pretrigger=True)
    hive.trigger(i.pull_value, i.build_conjugate)


Conjugate = hive.hive("Conjugate", build_conjugate)