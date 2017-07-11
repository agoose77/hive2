from dragonfly.bind import create_instantiator

import dragonfly
import hive
from dragonfly.event import EventManager, bind_info
from dragonfly.std import Variable


def build_some_instance(i, ex, args):
    i.some_var = hive.attribute("str")
    ex.on_tick = dragonfly.event.OnTick()
    i.mod = hive.modifier(lambda self: print(self, self._some_var))
    hive.connect(ex.on_tick, i.mod)

    def on_stopped():
        print("I am closed!")

    ex.on_closed = hive.plugin(on_stopped, "on_stopped")


Instantiator = create_instantiator(bind_info)
SomeHive = hive.hive("SomeHive", build_some_instance)


def build_my_hive(i, ex, args):
    ex.events = EventManager()

    # Create instantiator, but don't add events by leader
    ex.instantiator = Instantiator(forward_events='all')

    # Create args dict
    i.hive_class = Variable("class", start_value=SomeHive)
    hive.connect(i.hive_class, ex.instantiator.hive_class)


MyHive = hive.hive("MyHive", build_my_hive)
my_hive = MyHive()

my_hive.instantiator.create()
pid_a = my_hive.instantiator.last_process_id.pull()

my_hive.instantiator.create()
pid_b = my_hive.instantiator.last_process_id.pull()

my_hive.instantiator.create()
pid_c = my_hive.instantiator.last_process_id.pull()

my_hive.events.read_event.plugin()(("tick",))
print(pid_a, pid_b, pid_c)
print("Closing A!")
my_hive.instantiator.stop_process.push(pid_a)
#
# my_hive.events.read_event.plugin()(("tick",))