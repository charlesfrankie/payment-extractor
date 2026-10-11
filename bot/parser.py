"""Parse ABA payment notifications (USD / Riels) into structured data."""
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

PATTERN = re.compile(
    r"(?:(?P<label>Riels|Riel|KHR|USD)\s*:\s*)?(?P<sym>[៛$])\s*(?P<amount>[\d,]+(?:\.\d+)?)\s+"
    r"paid by\s+(?P<name>.+?)\s*\((?P<acct>\*?\d+)\)\s+"
    r"on\s+(?P<month>[A-Za-z]{3,9})\s+(?P<day>\d{1,2}),\s*(?P<hour>\d{1,2}):(?P<minute>\d{2})\s*(?P<ampm>[AaPp][Mm])\s+"
    r"via\s+(?P<via>.+?)\s+at\s+(?P<merchant>.+?)\.\s+"
    r"(?:Remark:\s*(?P<remark>.*?)\.?\s*Trx\.|Trx\.)\s*"
    r"ID:\s*(?P<trx>\d+)"
    r"(?:\s*,\s*APV:\s*(?P<apv>\d+))?",
    re.IGNORECASE | re.DOTALL,
)
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


@dataclass
class Payment:
    paid_at: str            # "YYYY-MM-DD HH:MM" (24h)
    account_name: str
    account_no: str
    usd: Optional[float]
    khr: Optional[int]
    bank: str
    merchant: str
    remark: str
    trx_id: str
    apv: str


def parse_payment(text: str, ref: Optional[datetime] = None) -> Optional[Payment]:
    """Return a Payment, or None if `text` isn't a payment notification.
    `ref` = when the Telegram message was posted (the bank text has no year)."""
    if not text:
        return None
    m = PATTERN.search(text.replace("\u200b", ""))
    if not m:
        return None
    ref = (ref or datetime.now()).replace(tzinfo=None)
    month = MONTHS.index(m["month"][:3].lower()) + 1 if m["month"][:3].lower() in MONTHS else None
    if month is None:
        return None
    hour = int(m["hour"]) % 12 + (12 if m["ampm"].upper() == "PM" else 0)
    day = int(m["day"])
    year = ref.year
    if datetime(year, month, day) - ref > timedelta(days=2):   # Dec payment read in January
        year -= 1
    amount = float(m["amount"].replace(",", ""))
    is_usd = m["sym"] == "$" or (m["label"] or "").upper() == "USD"
    return Payment(
        paid_at=f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{m['minute']}",
        account_name=re.sub(r"\s+", " ", m["name"]).strip(),
        account_no=m["acct"],
        usd=round(amount, 2) if is_usd else None,
        khr=None if is_usd else int(round(amount)),
        bank=m["via"].strip(),
        merchant=m["merchant"].strip(),
        remark=(m["remark"] or "").strip(),
        trx_id=m["trx"],
        apv=m["apv"] or "",
    )
