# KABot – Kleinanzeigen Scraper Bot

A Python bot that monitors [kleinanzeigen.de](https://www.kleinanzeigen.de) for new listings matching your search criteria and sends Telegram notifications when deals are found.

## Features

- Automatically searches for items based on configurable search queries
- Filters results by price range (min/max)
- Excludes irrelevant listings (e.g. wanted ads, damaged items)
- Sends Telegram notifications with listing details and link
- Tracks seen ads to avoid duplicate notifications
- Anti-bot detection measures (randomized delays, stealth browser mode)

## Requirements

- Python 3.8+
- [Playwright](https://playwright.dev/python/)
- A Telegram bot token and chat ID

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/nickhrnsch/KABot.git
   cd KABot
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

4. Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```

   Edit `.env`:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_CHAT_ID=your_telegram_chat_id
   KLEINANZEIGEN_BASE_URL=https://www.kleinanzeigen.de/s-{PLZ}/anbieter:privat/anzeige:angebote/{SUCHBEGRIFF}/k0l{ID}r50
   ```

## Usage

Run with default searches (`searches.json`):
```bash
python main.py
```

Run with a different search config:
```bash
python main.py --searches searches_kindle.json
```

## Configuration

**`config.json`** – Controls delay between scraping cycles (in minutes):
```json
{
  "settings": {
    "min_delay_minutes": 3,
    "max_delay_minutes": 7
  }
}
```

**`searches.json`** – Defines what to search for:
```json
[
  {
    "name": "MacBook Air M1",
    "query": "macbook air m1",
    "min_price": 200,
    "max_price": 300
  }
]
```
