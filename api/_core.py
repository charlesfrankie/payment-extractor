"""Telegram update -> parse -> store. Pure logic, no network (easy to test)."""
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from _parser import parse_payment

TZ = ZoneInfo(os.getenv("TIMEZONE", "Asia/Phnom_Penh"))


def process_update(update: dict, store, channel_id: str = "") -> str:
    msg = (update.get("channel_post") or update.get("edited_channel_post")
           or update.get("message") or update.get("edited_message"))
    if not msg:
        return "ignored"
    if channel_id and str(msg["chat"]["id"]) != str(channel_id):
        return "other chat"

    text = msg.get("text") or msg.get("caption") or ""
    sent = datetime.fromtimestamp(msg["date"], TZ).replace(tzinfo=None)
    payment = parse_payment(text, ref=sent)

    if payment is None:
        if "paid by" in text.lower():          # looks like a payment but format is new -> keep for review
            store.add_unparsed(text)
            return "unparsed"
        return "not a payment"
    if store.has_trx(payment.trx_id):
        return "duplicate"
    store.add_payment(payment)
    return "saved"
