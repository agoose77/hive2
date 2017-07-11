import hive


def do_decomposition(i, ex):
    value = i.value.value
    i.real.value = value.real
    i.imag.value = value.imag


def build_decompose(i, ex, args):
    """Decompose complex number into real and imaginary components"""
    i.value = hive.attribute('complex')
    i.real = hive.attribute('float')
    i.imag = hive.attribute('float')

    ex.real = i.real.pull_out
    ex.imag = i.imag.pull_out
    ex.value = i.value.pull_in

    i.do_decomposition = hive.modifier(do_decomposition)
    i.imag.pull_in.pre_triggered.connect(i.value.pull_in.trigger)
    i.real.pull_in.pre_triggered.connect(i.value.pull_in.trigger)
    i.value.pull_in.triggered.connect(i.do_decomposition.trigger)
    hive.trigger(i.pull_value, i.do_decomposition)


Decompose = hive.hive("Decompose", build_decompose)
