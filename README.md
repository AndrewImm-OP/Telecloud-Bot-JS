# Fork 
Forked from the original Python implementation to JavaScript/TypeScript for improved performance and ecosystem benefits:
  
  Better async performance: Node.js event loop provides more efficient handling of concurrent API requests and webhook processing compared to Python's asyncio
  
  Native Telegram Bot API libraries: Leveraging production-ready libraries like node-telegram-bot-api or telegraf with better TypeScript support and active maintenance
  
  Reduced latency: JavaScript's non-blocking I/O model delivers faster response times for bot interactions and file operations
  
  Enhanced scalability: More lightweight runtime memory footprint enables better scaling when handling multiple users simultaneously
  
  Development velocity: Faster iteration cycles with hot-reloading and broader package ecosystem for API integrations

# TeleCloud Bot
Original Telegram bot for using TeleCloud: https://t.me/otelecloud_bot
# Installation

1. Clone the repository `git clone https://github.com/AndrewImm-OP/Telecloud-Bot-JS`
2. Go to directory `cd telecloudbot`
3. Install requirements `npm install`
4. Create `.env` with contents:
```ini
TOKEN=TELEGRAM_BOT_TOKEN
LOCAL_TAPI=False
LOCAL_TAPI_URL=http://localhost:8081
```
5. Start bot using command `node main.js`

# Fix the limit on 20 MB download

1. Build `telegram-bot-api` using https://tdlib.github.io/telegram-bot-api/build.html for your OS
2. Run server using `./telegram-bot-api --local --api-id=<API-ID> --api-hash=<API-HASH>`
3. Edit `LOCAL_TAPI` from `False` to `True` and edit `LOCAL_TAPI_URL` to your local telegram-bot-api on `.env`

# Why?
  I love JS, and hate Python =D
