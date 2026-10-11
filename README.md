# Wedding gift payment logger (Python on Vercel)

Telegram channel -> Vercel function (app.py, Flask) -> Google Sheet "Payments Log" tab.

Environment variables (Vercel > Project > Settings > Environment Variables):
- SECRET            any letters/numbers/_/- (max 256); must equal secret_token used in setWebhook
- SHEET_ID          the part of the sheet URL between /d/ and /edit
- GOOGLE_CREDS_JSON the FULL contents of the service-account JSON key file
- CHANNEL_ID        optional, e.g. -1001234567890
- TAB_NAME          optional, default "Payments Log"
- TIMEZONE          optional, default Asia/Phnom_Penh

Connect Telegram (open in browser once, replace the CAPS parts):
https://api.telegram.org/botBOT_TOKEN/setWebhook?url=https://YOUR-APP.vercel.app/api/webhook&secret_token=SECRET&drop_pending_updates=true

Health check: open https://YOUR-APP.vercel.app/api/webhook -> "alive"
Logs: Vercel > Project > Logs

## Run locally first
    python -m venv venv && source venv/bin/activate      (Windows: venv\Scripts\activate)
    pip install -r requirements.txt
    cp .env.example .env     (Windows: copy .env.example .env)  -> fill in BOT_TOKEN, SHEET_ID, put service_account.json in this folder
    python run_local.py --samples --dry-run    # parsing test
    python run_local.py --samples              # Google Sheet test
    python run_local.py                        # real Telegram channel
