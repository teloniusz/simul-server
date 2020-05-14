from collections import namedtuple


_OPX_MSG = (
    ('UNKNOWN_OP', 'Unknown operation: {}'),
    ('PROCESS_RUNNING', 'Process is already running'),
    ('PROCESS_NOTRUNNING', 'Process is not running'),
    ('PROCESS_EXCEPTION', '{}: {}'),
    ('START_ERROR', 'Process start error'),
    ('PROCESS_ERROR', 'Process error')
)


OPX = namedtuple('OPX', [code for code, msg in _OPX_MSG])(*range(len(_OPX_MSG)))




class OpException(Exception):
    def __init__(self, code, *args, exception=None):
        self.code = code
        self.msg = _OPX_MSG[code][1].format(*args)
        self.exception=exception

    def __str__(self):
        return self.msg

    def __repr__(self):
        return '<OpException #{}: {}>'.format(self.code, self.msg)
