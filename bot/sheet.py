"""Google Sheets storage (service account)."""
import json
import os
from datetime import datetime

import gspread

from bot.core import TZ

HEADERS = ["Paid At", "Account Name", "Account No.", "USD ($)", "KHR (៛)", "Via Bank",
           "Merchant", "Remark", "Trx ID", "APV", "Logged At"]
TRX_COL = HEADERS.index("Trx ID") + 1
TAB = os.getenv("TAB_NAME", "Payments Log")
UNPARSED_TAB = "Unparsed"


class SheetStore:
    def __init__(self):
        info = json.loads(os.environ["GOOGLE_CREDS_JSON"])
        self.sh = gspread.service_account_from_dict(info).open_by_key(os.environ["SHEET_ID"])
        self.ws = self._tab(TAB, HEADERS)
        self._un = None

    def _tab(self, name, headers):
        try:
            return self.sh.worksheet(name)
        except gspread.WorksheetNotFound:
            ws = self.sh.add_worksheet(name, rows=1000, cols=len(headers))
            ws.append_row(headers)
            ws.freeze(rows=1)
            ws.format(f"A1:{chr(64 + len(headers))}1", {"textFormat": {"bold": True}})
            return ws

    @staticmethod
    def _now():
        return datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")

    def has_trx(self, trx_id):
        return trx_id in {v.strip() for v in self.ws.col_values(TRX_COL)[1:]}

    def add_payment(self, p):
        self.ws.append_row(
            [p.paid_at, p.account_name, p.account_no,
             p.usd if p.usd is not None else "", p.khr if p.khr is not None else "",
             p.bank, p.merchant, p.remark, "'" + p.trx_id, "'" + p.apv if p.apv else "", self._now()],
            value_input_option="USER_ENTERED")

    def add_unparsed(self, text):
        if self._un is None:
            self._un = self._tab(UNPARSED_TAB, ["Logged At", "Raw Message"])
        if text not in self._un.col_values(2):
            self._un.append_row([self._now(), text])
