import hive


def build_decompose(i, ex, args):
    """Decompose complex number into real and imaginary components"""
    i.value = hive.attribute('complex')
    i.real = hive.attribute('float')
    i.imag = hive.attribute('float')

    i.pull_imag = hive.pull_out(i.imag)
    i.pull_real = hive.pull_out(i.real)

    ex.real = hive.output(i.pull_real)
    ex.imag = hive.output(i.pull_imag)

    i.pull_value = hive.pull_in(i.value)
    ex.value = hive.antenna(i.pull_value)

    def build_value(self):
        value = self._value
        self._real = value.real
        self._imag = value.imag

    i.build_value = hive.modifier(build_value)

    hive.trigger(i.pull_imag, i.pull_value, pretrigger=True)
    hive.trigger(i.pull_real, i.pull_value, pretrigger=True)
    hive.trigger(i.pull_value, i.build_value)


Decompose = hive.hive("Decompose", build_decompose)