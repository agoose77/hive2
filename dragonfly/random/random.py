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

    @hive.return_type('float')
    def get_rand(self):
        return self.rng.random()

    @hive.return_type('bool')
    def get_bool(self):
        return self.get_rand() >= 0.5

    @hive.return_type('float')
    def get_randrange(self):
        return self.rng.randrange(self.randint_min, self.randint_max, self.randint_step)

    @hive.return_type('float')
    def get_uniform(self):
        return self.rng.uniform(self.uniform_min, self.uniform_max)


def build_random(cls, i, ex, args):
    """HIVE interface to Python random module"""
    i.push_seed = hive.push_in(cls.set_seed)
    ex.seed = hive.antenna(i.push_seed)

    i.pull_random = hive.pull_out(cls.get_rand)
    ex.random = hive.output(i.pull_random)

    i.pull_bool = hive.pull_out(cls.get_bool)
    ex.bool = hive.output(i.pull_bool)

    # Randint
    i.randint_min = hive.property(cls, "randint_min", "int")
    i.randint_max = hive.property(cls, "randint_max", "int")
    i.randint_step = hive.property(cls, "randint_step", "int")

    i.pull_randint_min = hive.pull_in(i.randint_min)
    i.pull_randint_max = hive.pull_in(i.randint_max)
    i.pull_randint_step = hive.pull_in(i.randint_step)

    ex.int_min = hive.antenna(i.pull_randint_min)
    ex.int_max = hive.antenna(i.pull_randint_max)
    ex.int_step = hive.antenna(i.pull_randint_step)

    i.pull_int = hive.pull_out(cls.get_randrange)
    ex.int = hive.output(i.pull_int)

    hive.trigger(i.pull_int, i.pull_randint_max, pretrigger=True)
    hive.trigger(i.pull_int, i.pull_randint_min, pretrigger=True)
    hive.trigger(i.pull_int, i.pull_randint_step, pretrigger=True)

    # Randrange
    i.uniform_min = hive.property(cls, "uniform_min", "float")
    i.uniform_max = hive.property(cls, "uniform_max", "float")

    i.uniform_min_in = hive.pull_in(i.uniform_min)
    i.uniform_max_in = hive.pull_in(i.uniform_max)

    ex.uniform_min = hive.antenna(i.uniform_min_in)
    ex.uniform_max = hive.antenna(i.uniform_max_in)

    i.pull_uniform = hive.pull_out(cls.get_uniform)
    ex.uniform = hive.output(i.pull_uniform)

    hive.trigger(i.pull_uniform, i.uniform_max_in, pretrigger=True)
    hive.trigger(i.pull_uniform, i.uniform_min_in, pretrigger=True)

Random = hive.hive("Random", build_random, drone_class=_RandomCls)
