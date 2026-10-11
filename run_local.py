"""
Run the payment logger on YOUR computer (no Vercel needed).

  python run_local.py --samples --dry-run   # 1) test parsing only (no Telegram, no Google)
  python run_local.py --samples             # 2) test Google Sheet connection with sample payments
  python run_local.py                       # 3) listen to your real Telegram channel and write to the sheet
  (add --dry-run to any of them to print instead of writing to Google)

Stop with Ctrl+C. Locally it asks Telegram for new messages (a webhook needs a public address).
"""
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))


def load_env():
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    creds = os.environ.get("GOOGLE_CREDS_FILE")
    if creds and "GOOGLE_CREDS_JSON" not in os.environ:
        os.environ["GOOGLE_CREDS_JSON"] = Path(creds).read_text(encoding="utf-8")


load_env()
from bot.core import process_update  # noqa: E402

SAMPLES = [
    "Riels: ៛27,000 paid by SUM KANYARAT (*993) on Oct 09, 03:36 PM via ABA PAY at TIM HOKTY. Trx. ID: 179153498026697, APV: 792581.",
    "USD: $3.00 paid by NOEUN CHANTHOEUN AND VAR CHANSOMNANG (*332) on Sep 22, 03:28 PM via ABA PAY at TIM HOKTY. Remark: . Trx. ID: 179006572883937, APV: 808680.",
    "៛20,000 paid by អ៊ុក ផាន្នីកា (*344) on Sep 17, 09:37 AM via ABA KHQR (ACLEDA Bank Plc.) at TIM HOKTY. Trx. ID: 178961262771803, APV: 743527.",
]


class PrintStore:
    """Dry-run store: prints what would be written to the sheet."""
    def __init__(self): self.seen = set()
    def has_trx(self, t): return t in self.seen
    def add_payment(self, p):
        self.seen.add(p.trx_id)
        amt = f"${p.usd:.2f}" if p.usd is not None else f"KHR {p.khr:,}"
        print(f"   WOULD SAVE -> {p.paid_at} | {p.account_name} | {amt} | {p.bank} | Trx {p.trx_id}")
    def add_unparsed(self, text): print("   WOULD SAVE TO 'Unparsed':", text[:80])


def make_store(dry):
    if dry:
        return PrintStore()
    from bot.sheet import SheetStore
    return SheetStore()


def fake_update(text):
    return {"channel_post": {"chat": {"id": 0}, "date": int(time.time()), "text": text}}


def telegram(token, method, **params):
    import requests
    r = requests.get(f"https://api.telegram.org/bot{token}/{method}", params=params, timeout=65)
    r.raise_for_status()
    return r.json()


def main():
    dry = "--dry-run" in sys.argv
    store = make_store(dry)

    if "--samples" in sys.argv:
        for text in SAMPLES:
            print(text[:60], "...")
            print("   result:", process_update(fake_update(text), store))
        return

    token = os.environ["BOT_TOKEN"]
    channel = os.environ.get("CHANNEL_ID", "")
    telegram(token, "deleteWebhook")           # getUpdates and a webhook can't be used together
    print("Listening to Telegram... post a payment in your channel. Ctrl+C to stop.")
    offset = 0
    while True:
        try:
            data = telegram(token, "getUpdates", offset=offset, timeout=30,
                            allowed_updates=json.dumps(["channel_post", "edited_channel_post", "message"]))
            for upd in data.get("result", []):
                text = ((upd.get("channel_post") or upd.get("message") or {}).get("text") or "")[:60]
                print(datetime.now().strftime("%H:%M:%S"), "message:", text)
                print("   result:", process_update(upd, store, channel))
                offset = upd["update_id"] + 1
        except KeyboardInterrupt:
            print("Stopped.")
            return
        except Exception as e:
            print("Error:", e, "- retrying in 5s")
            time.sleep(5)


if __name__ == "__main__":
    main()
