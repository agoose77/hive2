import hive


class QuitClass:

    def __init__(self):
        self._quit = None

    def set_quit(self, do_quit):
        self._quit = do_quit

    def quit(self):
        self._quit()


def build_quit(i, ex, args):
    """Quit the top-level Hive"""
    i.quit_drone = hive.drone(QuitClass)
    ex.get_quit = i.drone.set_quit.socket(identifier="quit")
    ex.do_quit = i.drone.quit.trigger


Quit = hive.hive("Quit", build_quit)
