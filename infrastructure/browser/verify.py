"""Exercise delegated form filling against an in-container, disposable fixture."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import threading
from urllib.parse import parse_qs

received = {}


class Form(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b'''<html><title>Local browser verification</title><h1>Local verification</h1>
        <form method="post"><label>Name<input name="name" required></label>
        <label>Email<input name="email" type="email" required></label>
        <button type="submit">Submit test</button></form></html>'''
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        received.update(parse_qs(self.rfile.read(int(self.headers['Content-Length'])).decode()))
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<h1>TEST-RECEIPT-OK</h1>')

    def log_message(self, *args):
        pass


server = ThreadingHTTPServer(('127.0.0.1', 0), Form)
threading.Thread(target=server.serve_forever, daemon=True).start()
port = server.server_address[1]
try:
    task = f'Open http://127.0.0.1:{port}/ . Fill Name as Browser Test and Email as test@example.invalid. Submit this local test form exactly once. Return the receipt heading. This is a disposable local fixture, not an external submission.'
    result = subprocess.run(['python', '/opt/browser/task.py'], input=task, text=True,
                            capture_output=True, timeout=220)
    passed = received == {'name': ['Browser Test'], 'email': ['test@example.invalid']}
    evidence = {'delegated_form_received_exact_values': passed, 'task_exit': result.returncode,
                'expected_receipt': 'TEST-RECEIPT-OK', 'provider': 'existing OpenCode Go',
                'external_form_submission': False}
    out = Path('/state/verification')
    out.mkdir(exist_ok=True)
    (out / 'form.json').write_text(json.dumps(evidence, indent=2))
    print(json.dumps(evidence))
    if not passed:
        print(result.stdout[-3000:])
        print(result.stderr[-1000:])
        raise SystemExit(1)
finally:
    server.shutdown()
