"""Vercel serverless function: Telegram webhook -> Google Sheet."""
import hmac
import json
import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(__file__))
from _core import process_update  # noqa: E402

_store = None


def get_store():
    global _store                      # reused while the function stays warm
    if _store is None:
        from _sheet import SheetStore
        _store = SheetStore()
    return _store


class handler(BaseHTTPRequestHandler):
    def _send(self, code, text):
        body = text.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send(200, "alive")

    def do_POST(self):
        secret = os.environ.get("SECRET", "")
        got = self.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not secret or not hmac.compare_digest(got, secret):
            return self._send(403, "forbidden")
        try:
            length = int(self.headers.get("Content-Length") or 0)
            update = json.loads(self.rfile.read(length) or b"{}")
            result = process_update(update, get_store(), os.environ.get("CHANNEL_ID", ""))
            print("result:", result)
            self._send(200, result)    # plain 200 = Telegram is happy, no retries
        except Exception:
            traceback.print_exc()
            self._send(500, "error")   # real failure (e.g. Google down): Telegram retries later
