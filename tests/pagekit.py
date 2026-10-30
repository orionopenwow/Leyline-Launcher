"""Shared bits for the browser page tests: is Playwright here, and a quiet local web server."""
import functools
import http.server
import threading

try:
    from playwright.sync_api import sync_playwright  # noqa: F401
    HAVE_PW = True
except ImportError:
    HAVE_PW = False


def serve(directory):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=directory))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/"
