#!/usr/bin/env python3
"""Expose only Pocket ID totals to the private Homepage dashboard."""

import json
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


DATABASE = Path("/var/lib/pocket-id/pocket-id.db")


def counts(database=DATABASE):
    # mode=ro includes current WAL state without permitting database writes.
    connection = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True, timeout=3)
    try:
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        return {
            "users": connection.execute("SELECT count(*) FROM users").fetchone()[0],
            "clients": connection.execute("SELECT count(*) FROM oidc_clients").fetchone()[0],
        }
    finally:
        connection.close()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/stats":
            self.send_error(404)
            return
        try:
            body = json.dumps(counts()).encode()
            status = 200
        except (OSError, ValueError, sqlite3.Error):
            body = b'{"error":"Pocket ID unavailable"}'
            status = 503
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format, *_args):
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("10.1.1.6", 1412), Handler).serve_forever()
