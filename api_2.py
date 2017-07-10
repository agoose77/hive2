import hive



class DroneClass:

    @property
    def x(self):
        return self._x

    def push_x(self, x):
        self._x = x


def build(cls, i, ex, args):
    i.x = cls.x
    ex.x = i.x.property()

    i.push_x = cls.push_x
    ex.push_x = i.push_x.push_in



H = hive.hive("build", build, drone_cls=DroneClass)
h = H()
