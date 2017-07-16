import hive



class DroneClass:
    def __init__(self, x):
        self._x = x

    @property
    def x(self):
        return self._x

    def push_x(self, x):
        self._x = x

    def debug(self):
        print(hive.args(self))
        print("DBG")


def mod(i, ex):
    print(i.drone)


def build(i, ex, args):
    args.name = hive.parameter("str")
    i.mod = hive.modifier(mod)
    i.drone = hive.drone(DroneClass, args.name)

    ex.x = i.drone.x.proxy()
    ex.t = i.mod.trigger
    ex.dbg = i.drone.debug.trigger


H = hive.hive("MyHive", build)
h = H("bill")

print(h.x)
h.dbg()