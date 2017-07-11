import hive


def build_compose(i, ex, args):
    """Compose complex number from real and imaginary components"""
    i.value = hive.attribute('complex')
    i.real = hive.attribute('float')
    i.imag = hive.attribute('float')

    i.pull_imag = hive.pull_in(i.imag)
    i.pull_real = hive.pull_in(i.real)

    ex.real = hive.antenna(i.pull_real)
    ex.imag = hive.antenna(i.pull_imag)

    i.pull_value = hive.pull_out(i.value)
    ex.value = hive.output(i.pull_value)

    def build_value(self):
        self._value = complex(self._real, self._imag)

    i.build_value = hive.modifier(build_value)

    hive.trigger(i.pull_value, i.pull_imag, pretrigger=True)
    hive.trigger(i.pull_imag, i.pull_real)
    hive.trigger(i.pull_real, i.build_value)


Compose = hive.hive("Compose", build_compose)
