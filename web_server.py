import argparse
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from posixpath import relpath
from pytz import UTC


mime_types = {
    ".css": "text/css",
    ".js": "text/javascript",
    ".htm": "text/html",
    ".ico": "image/x-icon",
    ".svg": "image/svg+xml"
}

def get_mime_type(path):
    extension = os.path.splitext(path)[1]
    if extension in mime_types:
        return mime_types[extension]
    return "text/plain"


public_path = None

class Handler(BaseHTTPRequestHandler):
    def get_handler(self, request):
        return None

    def do_GET(self):
        handler = self.get_handler(self.path)
        if(handler is not None):
            handler()
        elif self.path == "/":
            self.send_file("/index.htm")
        else:
            self.send_file(self.path)

    def send_file(self, path):
        path = relpath(path, "/")
        path = os.path.join(public_path, path)
        path = os.path.realpath(path)

        if not os.path.exists(path):
            print(f"Failed to find file '{path}'")
            self.send_response(404)
            return

        if not path.startswith(public_path):
            print(f"Attempt to access file outside of public path!: '{path}'")
            self.send_response(404)
            return

        self.send_response(200)
        self.send_header("Content-type", get_mime_type(path))
        self.end_headers()

        file = open(path, "rb")
        self.wfile.write(file.read())
        file.close()

def start(args, handler, in_public_path):
    global public_path
    public_path = in_public_path

    host_name = "" if args.remote else "localhost"
    server_port = args.port

    web_server = ThreadingHTTPServer((host_name, server_port), handler)
    web_server_thread = threading.Thread(target=web_server.serve_forever)
    web_server_thread.start()
    print("Started server at http://%s:%s" % (host_name, server_port))

def parse_args(description):
    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTION] function",
        description=description
    )

    parser.add_argument("-r", "--remote", action='store_true', help="Allow for remote access (rather than localhost).")
    parser.add_argument("-p", "--port", type=int, default=8080, help="Network port on which the server will listen." )

    return parser.parse_args()

