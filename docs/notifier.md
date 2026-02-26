# Notifier (Discord Notification System)

`notifier.py` provides a lightweight, dependency-free implementation for sending real-time notifications to Discord using Webhooks.

## Architecture & Principles
- **One Thing**: This module focuses solely on sending formatted alerts to Discord.
- **Dependency-Free**: Uses Python's standard `urllib.request` to avoid issues with external library versions (like `requests` or `httpx`).
- **Internal Env Loader**: Includes a minimal `.env` parser to load `DISCORD_WEBHOOK_URL` from `.env.local` automatically.

## Configuration
The notifier looks for the following variable in `.env.local` at the project root:
```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

## Features
- **Trade Notifications**: Sends color-coded Embeds for `BUY` (Green), `SELL` (Red), and `EXIT` (Gray/Result-based) actions.
- **Error Alerts**: Sends urgent system error logs with traceback snippets.
- **Formatting**: Uses Discord Embeds for high readability, including Symbol, Side, Price, and Quantity fields.

## Usage
### In Code
```python
from src.utils.notifier import DiscordNotifier

notifier = DiscordNotifier()
notifier.send_trade_notification("BUY", "BTCUSDT", 65000.0, 0.01)
notifier.send_error_notification("Something went wrong!")
```

### Manual Test
Run the manual test script to verify connection:
```bash
python3 tests/test_notifier_manual.py
```
