import threading

import hive as h
from .getch import change_termios, restore_termios, raw_input


class commandlineclass(object):
    command = None

    def __init__(self):
        self._commands = []
        self._listeners = []
        self._running = False

    def _new_command(self, command):
        self._commands.append(command)

    def start(self):
        if self._running: return

        def gcom(event, addcomfunc):
            try:
                while not event.is_set():
                    try:
                        com = raw_input(">>>")
                        if com != None:
                            addcomfunc(com)
                    except EOFError:
                        pass
            finally:
                restore_termios()

        change_termios()
        self.dead = threading.Event()
        t = threading.Thread(target=gcom, args=(self.dead, self._new_command,))
        t.daemon = True
        t.start()

    def stop(self):
        if self._running:
            self._running = False
            self.dead.set()

    def add_listener(self, listener):
        assert callable(listener), listener
        self._listeners.append(listener)

    def send_command(self, command):
        for listener in self._listeners:
            listener(command)

    def flush(self):
        for c in self._commands:
            self.send_command(c)
            self.command = c
            h.internal(self).push_command()
        self._commands = []


def build_commandline(i, ex, args):
    i.start = cls.start
    i.stop = cls.stop
    i.flush = cls.flush
    prop_command = h.property(cls, "command", "str")

    ex.prop_command = prop_command.proxy(h.READ)
    ex.command = prop_command.command.push_out
    ex.send_command = cls.send_command.trigger
    ex.start = i.start.trigger
    ex.flush = i.flush.trigger
    ex.stop = i.stop.trigger
    ex.listen = cls.add_listener.socket()


Commandline = h.hive("commandline", build_commandline, commandlineclass)
