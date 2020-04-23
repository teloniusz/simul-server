import os
import sys
import subprocess
import time
from .errors import OPX, OpException


class ProcessController:
    def __init__(self, command):
        self.command = command
        self.proc = None
        self.start_ts = None
        self.stop_ts = None
        self.exit_code = None
        self.start_lines = [0, 0]
        self.lines = [[], []]

    def _read_outs(self, timeout=None, stdin=None):
        "read all lines waiting in the internal buffer into self.lines[] table"

        outs, errs = self.proc.communicate(input=stdin, timeout=timeout)
        outs = outs.decode('utf-8')
        if outs.endswith('\n'):
            outs = outs[0:-1]
        errs = errs.decode('utf-8')
        if errs.endswith('\n'):
            errs = errs[0:-1]
        self.lines[0].extend(outs.split('\n'))
        self.lines[1].extend(errs.split('\n'))

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
            self.proc = subprocess.Popen(self.command,
                                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except exc:
            raise OpException(OPX.START_ERROR, exception=exc)

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

        results = [[], []]
        self._read_outs()
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
            min(len(lines)-1, last_lines[i])
            for i, lines in enumerate(self.lines)
        ]
        for i in (0, 1):
            self.start_lines[i] += indices[i]
            self.lines[i] = self.lines[i][indices[i]:]
            results[0].extend(self.lines[i])

        return results
