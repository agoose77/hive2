from random import Random as RNG

import hive


class _RandomCls:
    def __init__(self, seed=None):
        self.rng = RNG()
        self.rng.seed(seed)

        self.randint_min = None
        self.randint_max = None
        self.randint_step = None

        self.uniform_min = None
        self.uniform_max = None

    def set_seed(self, seed):
        self.rng.seed(seed)

    @hive.typed_property('float')
    def rand_float(self):
        return self.rng.random()

    @hive.typed_property('bool')
    def rand_bool(self):
        return self.rng.random() >= 0.5

    @hive.typed_property('float')
    def rand_range(self):
        return self.rng.randrange(self.randint_min, self.randint_max, self.randint_step)

    @hive.typed_property('float')
    def rand_uniform(self):
        return self.rng.uniform(self.uniform_min, self.uniform_max)


def build_random(i, ex, args):
    """HIVE interface to Python random module"""
    i.drone = hive.drone(_RandomCls)
    ex.rand_float = i.drone.rand_float.pull_out
    ex.bool = i.drone.rand_bool.pull_out

    # Randint
    i.randint_min = i.drone.property("randint_min", "int")
    i.randint_max = i.drone.property("randint_max", "int")
    i.randint_step = i.drone.property("randint_step", "int")

    ex.int_min = i.randint_min.pull_in
    ex.int_max = i.randint_max.pull_in
    ex.int_step = i.randint_step.pull_in
    ex.int = i.drone.rand_range.pull_out

    i.drone.rand_range.pull_out.before.connect(i.pull_randint_max.trigger,
                                               i.pull_randint_min.trigger,
                                               i.pull_randint_step.trigger)

    # Randrange
    i.uniform_min = i.drone.property("uniform_min", "float")
    i.uniform_max = i.drone.property("uniform_max", "float")

    ex.uniform_min = i.uniform_min.pull_in
    ex.uniform_max = i.uniform_max.pull_in

    ex.uniform = i.drone.rand_uniform.pull_out
    i.drone.rand_uniform.pull_out.before.connect(i.uniform_max.pull_in.trigger,
                                                 i.uniform_min.pull_in.trigger)


Random = hive.hive("Random", build_random)
