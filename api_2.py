import hive



class DroneClass:
    _x = 1

    @property
    def x(self):
        return self._x

    def push_x(self, x):
        self._x = x

    def debug(self):
        print("DBG")


def mod(i, ex):
    print(i.drone)


def build(i, ex, args):
    i.mod = hive.modifier(mod)
    i.drone = hive.drone(DroneClass)

    ex.x = i.drone.x.property()
    ex.t = i.mod.trigger
    ex.dbg = i.drone.debug.trigger


H = hive.hive("build", build)
h = H()

print(h.x)
h.t()
h.dbg()