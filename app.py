from .errors import OPX, OpException
from .process import ProcessController


class MainApp:
    def __init__(self, config):
        self.config = config
        try:
            self.name = config['server_name']
            self.command = config['command']
        except KeyError:
            raise Exception('Misconfiguration: server_name and command must be defined')
        self.controller = ProcessController(self.command)

    def handle_request(self, op, *params):
        result = {
            'server': self.name
        }
        try:
            res = self.run_request(op, *params)
        except OpException as ex:
            result['status'] = 'error'
            result['error'] = str(ex)
        else:
            result['status'] = 'ok'
            result['result'] = res
        return result

    def run_request(self, op, *params):
        try:
            op = getattr(self, 'op_' + op)
        except AttributeError:
            raise OpException(OPX.UNKNOWN_OP, op)
        try:
            result = op(*params)
        except OpException:
            raise
        except Exception as ex:
            raise OpException(OPX.PROCESS_EXCEPTION, ex.__class__.__name__, str(ex))
        return result

    def do_ping(self, *params):
        return 'pong'

    def do_start(self, *params):
        self.controller.start(*params)

    def do_status(self, *params):
        if self.controller.is_running:
            return {
                'status': 'running',
                'start': self.controller.start_ts
            }
        if self.controller.start_ts:
            return {
                'status': 'finished',
                'start': self.controller.start_ts,
                'stop': self.controller.stop_ts,
                'code': self.controller.exit_code
            }
        return {'status': 'idle'}

    def do_get_output(self, *params):
        if not self.controller.start_ts:
            raise OpException(OPX.PROCESS_NOTRUNNING)
        last_line = [0, 0]
        if len(params):
            try:
                last_lines = [int(params[0]), int(params[1])]
            except (ValueError, IndexError):
                raise ValueError('Last lines (stdout, sterr) number expected')

        return {'lines': self.controller.fetch_lines(last_lines)}

    def do_kill(self, *params):
        if not self.controller.start_ts:
            raise OpException(OPX.PROCESS_NOTRUNNING)
        if not self.controller.is_running:
            return {
                'status': 'finished',
                'start': self.controller.start_ts,
                'stop': self.controller.stop_ts,
                'code': self.controller.exit_code
            }
        self.controller.kill(*params)
        return {
            'status': 'killed',
            'start': self.controller.start_ts,
            'code': self.controller.exit_code
        }
