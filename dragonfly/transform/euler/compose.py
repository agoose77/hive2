import hive


def compose_modifier(self):
    self._result = (self._x, self._y, self._z)


def build_compose(i, ex, args):
    """Compose a euler from its x, y and z components"""
    i.compose_vector = hive.modifier(compose_modifier)

    i.result = hive.attribute("euler")
    i.pull_result = hive.pull_out(i.result)

    for name in ('x', 'y', 'z'):
        attr = hive.attribute("float")
        setattr(i, name, attr)

        pull_in = hive.pull_in(attr)
        setattr(ex, "{}".format(name), hive.antenna(pull_in))

        hive.trigger(i.pull_result, pull_in, pretrigger=True)

    hive.trigger(i.pull_result, i.compose_vector, pretrigger=True)
    ex.result = hive.output(i.pull_result)


Compose = hive.hive("Compose", build_compose)
