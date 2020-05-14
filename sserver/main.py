import json
from .config import ConfigReader
from .app import MainApp
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class AppMixin:
    def __init__(self):
        self.config = ConfigReader()
        self.app = MainApp(self.config)

    @staticmethod
    def valid_json(json_input):
        try:
            args_input = json.loads(json_input.decode('utf-8'))
        except UnicodeDecodeError:
            return 'Invalid unicode input'
        except json.decoder.JSONDecodeError as ex:
            return 'Invalid JSON input: ' + str(ex)
        if type(args_input) != list:
            return 'Invalid JSON input (expecting op argument array)'
        return args_input


class WSGIHandler(AppMixin):
    class Response:
        def __init__(self, code, ctype, content, head=False):
            self.headers = []
            self.body = ''
            content = content.encode('utf-8')
            self.code = code
            self.headers.append(("Content-type", ctype + '; charset=utf-8'))
            if content or not head:
                self.headers.append(("Content-length", len(content)))
            if not head:
                self.body = content

        def send(self, start_response):
            start_response(self.code, self.headers)
            return self.body

    def get_response(self, method, path, reader):
        if method != 'POST':
            return Response('405 Method Not Allowed', 'text/plain', 'Bad request method')

        args = self.valid_json(reader.read())
        if (type(args) == str):
            return Response('400 Bad Request', 'text/plain', args)

        result = self.app.handle_request(self.path[1:], *args)
        return Response(200, 'application/javascript', json.dumps(result))

    def __call__(self, environ, start_response):
        method = environ['REQUEST_METHOD']
        path = environ['PATH_INFO']
        reader = environ['wsgi.input']

        return [self.get_response(method, path, reader).send(start_response)]


class HTTPHandler(BaseHTTPRequestHandler, AppMixin):
    def __init__(self, *args, **kwargs):
        AppMixin.__init__(self)
        super().__init__(*args, **kwargs)

    def return_response(self, code, ctype, content, head=False):
        content = content.encode('utf-8', 'replace')
        self.send_response(code)
        self.send_header("Content-Type", ctype + '; charset=utf-8')
        if content or not head:
            self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        if not head:
            self.wfile.write(content)

    def do_POST(self):
        """Respond to a POST request."""
        try:
            clen = int(self.headers['Content-Length'])
        except:
            json_input = self.rfile.read()
        else:
            json_input = self.rfile.read(clen)
        args = self.valid_json(json_input)
        if type(args) == str:
            self.return_response(400, 'text/plain', args)
        else:
            result = self.app.handle_request(self.path[1:], *args)
            self.return_response(200, 'application/javascript', json.dumps(result))


app = WSGIHandler()


if __name__ == '__main__':
    httpd = ThreadingHTTPServer(('0.0.0.0', 8000), HTTPHandler)
    try:
        print("Serving: http://localhost:8000/")
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
