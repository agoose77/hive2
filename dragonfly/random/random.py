from random import Random as RNG

import hive


class RandomClass:
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


def build_random(cls, i, ex, args):
    """HIVE interface to Python random module"""
    # i.push_seed = hive.push_in(cls.set_seed)
    # ex.seed = hive.antenna(i.push_seed)
    i.random_drone = hive.drone(RandomClass)
    ex.rand_float = i.random_drone.rand_float.pull_out
    ex.bool = i.random_drone.rand_bool.pull_out

    # Randint
    i.randint_min = i.random_drone.property("randint_min", "int")
    i.randint_max = i.random_drone.property("randint_max", "int")
    i.randint_step = i.random_drone.property("randint_step", "int")

    ex.int_min = i.randint_min.pull_in
    ex.int_max = i.randint_max.pull_in
    ex.int_step = i.randint_step.pull_in
    ex.int = i.random_drone.rand_range.pull_out

    i.random_drone.rand_range.pull_out.pre_pushed.connect(i.pull_randint_max.trigger,
                                                          i.pull_randint_min.trigger,
                                                          i.pull_randint_step.trigger)

    # Randrange
    i.uniform_min = i.random_drone.property("uniform_min", "float")
    i.uniform_max = i.random_drone.property("uniform_max", "float")

    ex.uniform_min = i.uniform_min.pull_in
    ex.uniform_max = i.uniform_max.pull_in

    ex.uniform = i.random_drone.rand_uniform.pull_out
    i.random_drone.rand_uniform.pull_out.pre_pushed.connect(i.uniform_max.pull_in.trigger,
                                                            i.uniform_min.pull_in.trigger)


Random = hive.hive("Random", build_random)
