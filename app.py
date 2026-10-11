"""Vercel entrypoint (Flask): Telegram webhook -> Google Sheet.
Endpoint: https://YOUR-APP.vercel.app/api/webhook
"""
import hmac
import os
import traceback

from flask import Flask, request

from bot.core import process_update

app = Flask(__name__)
_store = None


def get_store():
    global _store                       # reused while the function stays warm
    if _store is None:
        from bot.sheet import SheetStore
        _store = SheetStore()
    return _store


@app.get("/")
@app.get("/api/webhook")
def alive():                            # open the URL in a browser -> "alive"
    return "alive"


@app.post("/api/webhook")
def webhook():
    secret = os.environ.get("SECRET", "")
    got = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not secret or not hmac.compare_digest(got, secret):
        return "forbidden", 403
    try:
        update = request.get_json(force=True, silent=True) or {}
        result = process_update(update, get_store(), os.environ.get("CHANNEL_ID", ""))
        print("result:", result)
        return result, 200              # plain 200 = Telegram is happy, no retries
    except Exception:
        traceback.print_exc()
        return "error", 500             # real failure (e.g. Google down): Telegram retries later
