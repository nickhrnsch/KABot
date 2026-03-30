import json
import time
import random
import os
import logging
import argparse
from dotenv import load_dotenv
from urllib.parse import quote
from scraper import fetch_and_parse
from notifier import send_telegram_message

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ]
)
logger = logging.getLogger(__name__)

CONFIG_FILE = "config.json"

def load_config(searches_file):
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
    if "settings" not in config:
        raise ValueError(f"Fehlender Pflichtschlüssel in config.json: 'settings'")
    with open(searches_file, "r", encoding="utf-8") as f:
        searches = json.load(f)
    for search in searches:
        if "query" not in search or "max_price" not in search:
            raise ValueError(f"Ungültiger Such-Eintrag (query/max_price fehlt): {search}")
    config["searches"] = searches
    return config

def run_scraper_cycle(searches_file):
    config = load_config(searches_file)
    logger.info("=" * 50)
    logger.info("Starte neuen Durchlauf...")

    base_url = os.getenv("KLEINANZEIGEN_BASE_URL")
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not base_url:
        logger.error("KLEINANZEIGEN_BASE_URL fehlt in der .env Datei.")
        return 60
    if not bot_token or not chat_id:
        logger.error("TELEGRAM_BOT_TOKEN oder TELEGRAM_CHAT_ID fehlt in der .env Datei.")
        return 60

    searches = config["searches"]
    random.shuffle(searches) # Such-Reihenfolge zufällig durchmischen

    for search in searches:
        query = search["query"]
        min_price = search.get("min_price", 0)
        max_price = search["max_price"]

        # Leerzeichen durch Bindestriche ersetzen für die URL
        formatted_query = quote(query.replace(" ", "-"))

        # Kleinanzeigen Preis-Filter direkt in die URL als Slug integrieren
        price_slug = f"preis:{min_price}:{max_price}/"
        url = base_url.replace("{SUCHBEGRIFF}", price_slug + formatted_query)

        logger.info(f"Suche nach '{query}' ({min_price}€ - {max_price}€)")
        deals = fetch_and_parse(url, query, min_price, max_price, config)

        for deal in deals:
            logger.info(f"Neuer Deal: {deal['title']} für {deal['price']}€")
            msg = (
                f"🚨 <b>Neuer Apple Deal!</b>\n\n"
                f"<b>Gerät:</b> {deal['title']}\n"
                f"<b>Preis:</b> {deal['price']}€ (Dein Limit: {max_price}€)\n"
                f"<b>Eingestellt:</b> {deal['date']}\n\n"
                f"<a href='{deal['link']}'>Hier klicken zur Anzeige</a>"
            )
            send_telegram_message(bot_token, chat_id, msg)

        # Random delay zwischen den Suchbegriffen (7-15 Sekunden)
        time.sleep(random.uniform(7.0, 15.0))

    # Nächster Zyklus berechnen
    min_m = config["settings"]["min_delay_minutes"]
    max_m = config["settings"]["max_delay_minutes"]
    sleep_time = random.uniform(min_m * 60, max_m * 60)
    logger.info(f"Durchlauf beendet. Nächster Suchlauf in {sleep_time/60:.1f} Minuten.")
    return sleep_time

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--searches", default="searches.json", help="Searches-Datei (z.B. searches_kindle.json)")
    args = parser.parse_args()

    logger.info(f"Apple Reselling Bot wird gestartet... (Suchen: {args.searches}) (Abbruch mit STRG+C)")
    logger.info("Bitte das Playwright Chromium-Fenster ignorieren. Es ist nötig für die Erkennung.")

    while True:
        try:
            sleep_sec = run_scraper_cycle(args.searches)
            time.sleep(sleep_sec)
        except KeyboardInterrupt:
            logger.info("Bot beendet durch Nutzer.")
            break
        except Exception as e:
            logger.error(f"Schwerer Fehler: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
