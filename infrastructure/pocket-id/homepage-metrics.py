#!/usr/bin/env python3
"""Expose only Pocket ID totals to the private Homepage dashboard."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen


API_KEY = Path("/etc/pocket-id/homepage-metrics.key").read_text().strip()
API_URL = "http://127.0.0.1:1411/api"


def total(path):
    request = Request(
        f"{API_URL}/{path}?pagination%5Blimit%5D=1",
        headers={"X-API-KEY": API_KEY, "Accept": "application/json"},
    )
    with urlopen(request, timeout=3) as response:
        count = json.load(response)["pagination"]["totalItems"]
    if not isinstance(count, int) or count < 0:
        raise ValueError("invalid total")
    return count


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/stats":
            self.send_error(404)
            return
        try:
            body = json.dumps({"users": total("users"), "clients": total("oidc/clients")}).encode()
            status = 200
        except (OSError, ValueError, KeyError, TypeError):
            body = b'{"error":"Pocket ID unavailable"}'
            status = 503
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format, *_args):
        pass


ThreadingHTTPServer(("10.1.1.6", 1412), Handler).serve_forever()
