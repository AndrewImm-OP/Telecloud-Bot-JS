# TeleCloud Bot
Telegram bot for using TeleCloud
Example: https://t.me/otelecloud_bot
# Installation

1. Clone the repository `git clone https://github.com/ImSkaiden/telecloud_bot`
2. Go to directory `cd telecloudbot`
3. Install requirements `pip install -r requirements.txt`
4. Create `.env` with contents:
```ini
TOKEN=TELEGRAM_BOT_TOKEN
LOCAL_TAPI=False
LOCAL_TAPI_URL=http://localhost:8081
```
5. Start bot using command `python3 main.py`

# Fix the limit on 20 MB download

1. Build `telegram-bot-api` using https://tdlib.github.io/telegram-bot-api/build.html for your OS
2. Run server using `./telegram-bot-api --local --api-id=<API-ID> --api-hash=<API-HASH>`
3. Edit `LOCAL_TAPI` from `False` to `True` and edit `LOCAL_TAPI_URL` to your local telegram-bot-api on `.env`
