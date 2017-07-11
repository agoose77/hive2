import hive


def build_value(i, ex):
    i.value.value = complex(i.real.value, i.imag.value)


def build_compose(i, ex, args):
    """Compose complex number from real and imaginary components"""
    i.value = hive.attribute('complex')
    i.real = hive.attribute('float')
    i.imag = hive.attribute('float')

    ex.real = i.real.pull_in
    ex.imag = i.imag.pull_in
    ex.value = i.value.pull_out

    i.build_value = hive.modifier(build_value)

    i.value.pull_out.pre_triggered.connect(i.real.pull_in.trigger,
                                           i.imag.pull_in.trigger,
                                              i.build_value.trigger)


Compose = hive.hive("Compose", build_compose)
