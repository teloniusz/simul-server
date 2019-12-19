import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class ForkHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        """Respond to a GET request."""
        #self.send_response(200)
        #self.send_header("Content-type", "application/json")
        #self.end_headers()
        #self.wfile.write("<html><head><title>Title goes here.</title></head>")
        #self.wfile.write("<body><p>This is a test.</p>")

        # If someone went to "http://something.somewhere.net/foo/bar/",
        # then self.path equals "/foo/bar/".
        # self.wfile.write("<p>You accessed path: %self</p>" % self.path)
        # self.wfile.write("</body></html>")

        if self.path in ('/start', '/status', '/cancel'):
            try:
                result = {"response": self.handle_fork(self.path[1:])}
            except Exception as ex:
                result = {"error": str(ex)}
            resp = json.dumps(result).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-type", "application/javascript")
            self.send_header("Content-length", len(resp))
            self.end_headers()
            self.wfile.write(resp)
        else:
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write("<html><head><title>Not found.</title></head>".encode('utf-8'))
            self.wfile.write(("<body><p>Operation not found: %s.</p></body>" % self.path).encode('utf-8'))

    def handle_fork(self, op):
        return {}



if __name__ == '__main__':
    httpd = ThreadingHTTPServer(('0.0.0.0', 8000), ForkHandler)
    try:
        print("Serving: http://localhost:8000/")
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
