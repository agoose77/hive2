import select
import subprocess
import time

import chesskeeper


def parse_move(move, turn):
    fr, to, special = chesskeeper.parse_move(move, turn)
    if special in("O-O", "0-0"):
        if turn == "White":
            return "e1g1"
        else:
            return "e8g8"
    if special in("O-O-O", "0-0-0"):
        if turn == "White":
            return "e1c1"
        else:
            return "e8c8"
    columns = ("a", "b", "c", "d", "e", "f", "g", "h")
    row_fr = fr[1]
    col_fr = fr[0]
    row_to = to[1]
    col_to = to[0]
    ret = "%s%s%s%s" % (
        columns[col_fr], row_fr + 1, columns[col_to], row_to + 1)
    if special in ("Q", "R", "N", "B"):
        ret += special.lower()
    return ret


class UCIChessEngine(object):

    def __init__(self, engine_binary, engine_dir=None):
        self.engine_binary = engine_binary
        self.engine = subprocess.Popen(
            shell=True,
            args=engine_binary,
            cwd=engine_dir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            close_fds=True,
        )
        self.engine.stdin.write("uci\n")
        self._poll_until("uciok", 10)
        self.engine.stdin.write("ucinewgame\n")
        self.engine.stdin.write("isready\n")
        self._poll_until("readyok", 10)
        self.turn = "White"
        self.allmoves = ""

    def _poll_until(self, untilstr, timeout):
        lines = []
        while 1:
            try:
                ready = select.select([self.engine.stdout], [], [], timeout)
                if not len(ready[0]) or ready[0][0] != self.engine.stdout:
                    raise IOError("%s: timeout until '%s'" %
                                  (self.engine_binary, untilstr))
            except select.error:
                pass
            line = self.engine.stdout.readline().rstrip("\n")
            lines.append(line)
            if line.startswith(untilstr.rstrip("\n")):
                break
        return lines

    def get_move(self):
        self.engine.stdin.write("go\n")
        bestmove = self._poll_until("bestmove", 30)[-1]
        move = bestmove.split()[1]
        return move[:2] + "-" + move[2:]

    def make_move(self, move):
        parsedmove = parse_move(move, self.turn)
        self.allmoves += " " + parsedmove
        s = "position startpos moves%s" % self.allmoves
        self.engine.stdin.write(s + "\n")
        self.engine.stdin.write("isready\n")
        self._poll_until("readyok", 10)
        if self.turn == "White":
            self.turn = "Black"
        else:
            self.turn = "White"

    def terminate(self):
        self.engine.terminate()
        wait = 5
        waited = 0
        interval = 0.1
        while waited < wait:
            time.sleep(interval)
            waited += interval
            if self.engine.poll():
                break
        if waited >= wait:
            self.engine.kill()
