import os
import sys
import subprocess
import select
from fcntl import fcntl, F_GETFL, F_SETFL
import time
from .errors import OPX, OpException


class ProcessController:

    controllers = {}

    @classmethod
    def get_controller(cls, command):
        key = tuple(command)
        try:
            obj = cls.controllers[key]
        except KeyError:
            cls.controllers[key] = obj = cls(command)
        return obj

    def __init__(self, command):
        self.command = command
        self.proc = None
        self.poll = None
        self.start_ts = None
        self.stop_ts = None
        self.exit_code = None
        self.start_lines = [0, 0]
        self.lines = [[], []]

    def _read_outs(self, timeout=None, stdin=None):
        "read all lines waiting in the internal buffer into self.lines[] table"

        outputs = [b'', b'']
        fds = (self.proc.stdout.fileno(), self.proc.stderr.fileno())
        fd_keys = {fileno: idx for idx, fileno in enumerate(fds)}

        ready = True
        while ready:
            ready = self.poll.poll(0)
            for fd, _ in ready:
                idx = fd_keys[fd]
                outputs[idx] = os.read(fd, 1024)

        for idx, out in enumerate(outputs):
            out = out.decode('utf-8')
            if out.endswith('\n'):
                out = out[0:-1]
            lines = out.split('\n') if out else []
            print("  outs[%d]:" % idx, "'%s'" % out, lines)
            self.lines[idx].extend(lines)

    def _cleanup(self):
        "assumes process just finished"

        if not self.proc:
            return
        self._read_outs()
        self.stop_ts = time.time()

    @property
    def is_running(self):
        if self.stop_ts:
            return False
        if not self.proc:
            return False
        ret = self.proc.poll()
        if ret is None:
            return True
        self._cleanup()
        return False

    def start(self, *params):
        if self.is_running:
            raise OpException(OPX.PROCESS_RUNNING)
        self.stop_ts = None
        self.start_ts = time.time()
        try:
            self.proc = subprocess.Popen(
                self.command,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except exc:
            raise OpException(OPX.START_ERROR, exception=exc)
        fcntl(self.proc.stdout, F_SETFL, fcntl(self.proc.stdout, F_GETFL) | os.O_NONBLOCK)
        fcntl(self.proc.stderr, F_SETFL, fcntl(self.proc.stderr, F_GETFL) | os.O_NONBLOCK)
        self.poll = select.poll()
        self.poll.register(self.proc.stdout, select.POLLIN)
        self.poll.register(self.proc.stderr, select.POLLIN)

    def kill(self, kill=False):
        if self.proc:
            if not kill:
                self.proc.terminate()
            else:
                self.proc.kill()

    def fetch_lines(self, last_lines, stdin=None):
        """
        send stdin (optional)
        return stdout and stderr assuming last_lines are (stdout, stderr) last lines successfully read
        drop the buffer already read (indices < last line)
        """

        if not last_lines:
            last_lines = self.start_lines[:]
        results = [[], []]
        print("data before:", self.lines)
        self._read_outs(0.5, stdin)
        print("data after: ", self.lines)
        print("read start:", self.start_lines, last_lines)
        if last_lines[0] < self.start_lines[0]:
            print("Warning: requested stdout line %d, available lines from %d" % (
                last_lines[0], self.start_lines[0]))
            results[0] = ['' for _ in range(self.start_lines[0] - last_lines[0])]
            last_lines[0] = self.start_lines[0]
        if last_lines[1] < self.start_lines[1]:
            print("Warning: requested stderr line %d, available lines from %d" % (
                last_lines[1], self.start_lines[1]))
            results[1] = ['' for _ in range(self.start_lines[1] - last_lines[1])]
            last_lines[1] = self.start_lines[1]
        indices = [
            min(len(lines), last_lines[i])
            for i, lines in enumerate(self.lines)
        ]
        print("indices:", indices)
        for i in (0, 1):
            self.start_lines[i] += indices[i]
            self.lines[i] = self.lines[i][indices[i]:]
            results[0].extend(self.lines[i])

        return {
            "lines": results,
            "next": [lnum + len(results[idx])
                     for idx, lnum in enumerate(self.start_lines)]
        }
