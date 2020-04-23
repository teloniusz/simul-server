from collections import namedtuple


OPX = namedtuple('OPX', [
    'UNKNOWN_OP', 'PROCESS_RUNNING', 'PROCESS_NOTRUNNING',
    'PROCESS_EXCEPTION', 'START_ERROR', 'PROCESS_ERROR']
)(
    'Unknown operation: {}',
    'Process is already running',
    'Process is not running',
    '{}: {}',
    'Process start error',
    'Process error'
)


class OpException:
    def __init__(self, code, *args, exception=None):
        self.code = code
        self.msg = self.OPX[code].format(*args)
        self.exception=exception

    def __str__(self):
        return self.msg

    def __repr__(self):
        return '<OpException #{}: {}>'.format(self.code, self.msg)
