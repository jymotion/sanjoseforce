#!/usr/bin/env python3
"""Local preview that resolves URLs the way GitHub Pages does.

    python3 serve.py [port]      # default 8000

`python -m http.server` only serves exact paths, so every extensionless link
404s locally even though it works in production. This adds the two rules Pages
applies: try `<path>.html`, and fall back to 404.html with a real 404 status.
"""

import functools
import http.server
import pathlib
import socketserver
import sys

ROOT = pathlib.Path(__file__).parent


class Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        local = pathlib.Path(super().translate_path(path))
        if local.is_dir():
            index = local / "index.html"
            if index.is_file():
                return str(index)
        if not local.exists() and not local.suffix:
            for candidate in (local.with_suffix(".html"), local / "index.html"):
                if candidate.is_file():
                    return str(candidate)
        return str(local)

    def send_error(self, code, message=None, explain=None):
        if code == 404 and (ROOT / "404.html").is_file():
            body = (ROOT / "404.html").read_bytes()
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)
            return
        super().send_error(code, message, explain)

    def log_message(self, fmt, *args):
        sys.stderr.write("  %s\n" % (fmt % args))


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    socketserver.TCPServer.allow_reuse_address = True
    handler = functools.partial(Handler, directory=str(ROOT))
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"serving {ROOT} at http://localhost:{port}  (Ctrl-C to stop)")
        httpd.serve_forever()
