import hive


class _Quit:

    def __init__(self):
        self._quit = None

    def set_quit(self, do_quit):
        self._quit = do_quit

    def quit(self):
        self._quit()


def build_quit(cls, i, ex, args):
    """Quit the top-level Hive"""
    ex.get_quit = cls.set_quit.socket(identifier="quit")
    ex.do_quit = cls.quit.trigger


Quit = hive.hive("Quit", build_quit, drone_class=_Quit)
