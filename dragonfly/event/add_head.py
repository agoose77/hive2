import hive


def do_add_head(self):
    self._event = (self._head,) + self._leader


def build_add_head(i, ex, args):
    """Add header to event tuple"""
    i.do_add_head = hive.modifier(do_add_head)

    i.head = hive.attribute("str")
    i.pull_head = hive.pull_in(i.head)
    ex.head = hive.antenna(i.pull_head)

    i.leader = hive.attribute("tuple.event")
    i.pull_leader = hive.pull_in(i.leader)
    ex.leader = hive.antenna(i.pull_leader)

    i.event = hive.attribute("tuple.event")
    i.pull_event = hive.pull_out(i.event)
    ex.event = hive.output(i.pull_event)

    hive.trigger(i.pull_event, i.pull_head, pretrigger=True)
    hive.trigger(i.pull_head, i.pull_leader)
    hive.trigger(i.pull_leader, i.do_add_head)


AddHead = hive.hive("AddHead", build_add_head)
