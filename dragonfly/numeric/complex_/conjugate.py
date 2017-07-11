import hive


def do_conjugate(i, ex):
    i.conjugate.value = i.value.value.conjugate()


def build_conjugate(i, ex, args):
    """Calculate the complex conjugate of a complex number"""
    i.value = hive.attribute('complex')
    i.conjugate = hive.attribute('complex')

    ex.conjugate = i.conjugate.pull_out
    ex.value = i.value.pull_in

    i.do_conjugate = hive.modifier(do_conjugate)
    i.conjugate.pull_out.pre_triggered.connect(i.value.pull_in.trigger,
                                                  i.do_conjugate.trigger)


Conjugate = hive.hive("Conjugate", build_conjugate)

