import hive



class DroneClass:
    @property
    def foo(self):
        return 'x'

    def print_foo(self):
        print("Printing foo", self.foo)

    def set_plugin(self, p):
        print("Plugin", p)
        p()


def on_attr_updated(i, ex):
    print("attr updated!", i.attr.value)


def on_attr_updated_pre(i, ex):
    print("attr pre-updated!", i.attr.value)


def on_attr_pulled_in(i, ex):
    print("attr pull invoked!")


def on_attr_pulled_out(i, ex):
    print("attr pulled out!")


def do_pull(i, ex):
    print("invoking pull of attr")


def build(i, ex, args):
    i.cls = hive.drone(DroneClass)
    i.attr = hive.attribute("int", 0)

    i.pre_updated = hive.modifier(on_attr_updated_pre)
    i.attr.pre_updated.connect(i.pre_updated.trigger)

    i.updated = hive.modifier(on_attr_updated)
    i.attr.updated.connect(i.updated.trigger)

    i.on_attr_pulled_out = hive.modifier(on_attr_pulled_out)
    i.attr.pull_out.after.connect(i.on_attr_pulled_out.trigger)

    i.on_attr_pulled_in = hive.modifier(on_attr_pulled_in)
    i.attr.pull_in.after.connect(i.on_attr_pulled_in.trigger)

    i.do_pull = hive.modifier(do_pull)
    i.do_pull.pre_triggered.connect(i.attr.pull_in.trigger)

    ex.foo = i.cls.foo.proxy()

    ex.value = i.attr.proxy(hive.WRITE)

    ex.do_pull = i.do_pull.trigger
    ex.value_in = i.attr.pull_in

    ex.value_out = i.attr.pull_out
    ex.print_foo = i.cls.print_foo.trigger

    ex.plug = i.updated.trigger.plugin()
    # ex.sock = hive.socket(cls.set_plugin)


H = hive.hive("build", build)
h = H()
h2 = H()

hive.connect(h,h2)
# h.value_out.connect(h2.value_in)

h.value = 99
h2.value = 10

print(h2.value_out())

h2.do_pull()
print(h2.value_out())

print(h2.plug.plugin()())
