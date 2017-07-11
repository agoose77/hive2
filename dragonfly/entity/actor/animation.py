import hive


class AnimationClass:

    def __init__(self):
        self.current_frame = 0
        self.start_frame = 0
        self.end_frame = 0

        self._hive = hive.get_run_hive()

    def start(self):
        self._hive.start_frame()
        self._hive.end_frame()

        raise NotImplementedError

    def stop(self):
        raise NotImplementedError


def declare_animation(meta_args):
    meta_args.mode = hive.parameter("str", "single", options={"single", "loop"})


def build_animation(cls, i, ex, args, meta_args):
    """Play animation for actor"""
    i.do_start = hive.triggerable(cls.start)
    i.do_stop = hive.triggerable(cls.stop)

    ex.start = hive.entry(i.do_start)
    ex.stop = hive.entry(i.do_stop)

    i.current_frame = hive.property(cls, "current_frame", "int")
    i.end_frame = hive.property(cls, "end_frame", "int")
    i.start_frame = hive.property(cls, "start_frame", "int")

    i.pull_current_frame = hive.pull_out(i.current_frame)
    i.pull_end_frame = hive.pull_in(i.end_frame)
    i.pull_start_frame = hive.pull_in(i.start_frame)

    ex.current_frame = hive.output(i.pull_current_frame)
    ex.start_frame = hive.antenna(i.pull_start_frame)
    ex.end_frame = hive.antenna(i.pull_end_frame)


Animation = hive.dyna_hive("Animation", build_animation, declarator=declare_animation, drone_class=AnimationClass)