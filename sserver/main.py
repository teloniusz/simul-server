import json
from .config import ConfigReader
from .app import MainApp
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class WSGIHandler:
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


    def __init__(self):
        self.config = ConfigReader()
        self.app = MainApp(self.config)

    def get_response(self, method, path, reader):
        if method != 'POST':
            return Response('405 Method Not Allowed', 'text/plain', 'Bad request method')
        json_input = reader.read()
        try:
            args = json.loads(json_input.decode('utf-8'))
        except UnicodeDecodeError:
            return Response('400 Bad Request', 'text/plain', 'Invalid unicode input')
        if type(args_input) != list:
            return Response('400 Bad Request', 'text/plain', 'Invalid JSON input (expecting op argument array)')
        result = self.app.handle_request(self.path[1:], *args)
        return Response(200, 'application/javascript', json.dumps(result))

    def __call__(self, environ, start_response):
        method = environ['REQUEST_METHOD']
        path = environ['PATH_INFO']
        reader = environ['wsgi.input']

        return [self.get_response(method, path, reader).send(start_response)]


class HTTPHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.config = ConfigReader()
        self.app = MainApp(self.config)
        super().__init__(*args, **kwargs)

    def valid_json(self):
        json_input = self.rfile.read()
        try:
            args_input = json.loads(json_input.decode('utf-8'))
        except UnicodeDecodeError:
            return 'Invalid unicode input'
        if type(args_input) != list:
            return 'Invalid JSON input (expecting op argument array)'
        return args_input

    def return_response(self, code, ctype, content, head=False):
        content = content.encode('utf-8')
        self.send_response(code)
        self.send_header("Content-type", ctype + '; charset=utf-8')
        if content or not head:
            self.send_header("Content-length", len(content))
        self.end_headers()
        if not head:
            self.wfile.write(content)

    def do_POST(self):
        """Respond to a POST request."""

        args = self.valid_json()
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
