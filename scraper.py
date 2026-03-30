import time
import random
import logging
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import json
import os

logger = logging.getLogger(__name__)

SEEN_ADS_FILE = 'seen_ads.json'
MAX_SEEN = 10000

try:
    with open(SEEN_ADS_FILE, 'r', encoding='utf-8') as f:
        seen_ads = set(json.load(f))
except (FileNotFoundError, json.JSONDecodeError):
    seen_ads = set()

def fetch_and_parse(url, db_query, db_min_price, db_max_price, config):
    new_deals = []

    try:
        with Stealth().use_sync(sync_playwright()) as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-gpu",
                ]
            )
            try:
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    viewport={'width': 1920, 'height': 1080}
                )
                page = context.new_page()

                logger.info(f"Rufe Kleinanzeigen auf für Suche: '{db_query}'...")

                page.goto(url, timeout=30000)
                logger.info(f"Using URL: {url}")
                time.sleep(random.uniform(4.0, 7.0)) # Wartezeit, um Bot-Schutz zu reduzieren

                content = page.content()

                # Check auf Bot-Protection
                if "Zur Überprüfung, ob Sie ein echter Mensch sind" in content or "cloudflare" in content.lower():
                    logger.warning(f"Kleinanzeigen hat uns für '{db_query}' blockiert! ProtonVPN-Server wechseln, falls es dauerhaft passiert.")
                    return new_deals

                soup = BeautifulSoup(content, "html.parser")
                ad_items = soup.find_all("article", class_="aditem")

                for item in ad_items:
                    ad_id = item.get("data-adid")
                    if not ad_id or ad_id in seen_ads:
                        continue

                    title_elem = item.find("a", class_="ellipsis")
                    price_elem = item.find("p", class_="aditem-main--middle--price-shipping--price")
                    link_elem = item.find("a", href=True)
                    date_elem = item.find("div", class_="aditem-main--top--right")

                    if not title_elem or not price_elem:
                        continue

                    title = title_elem.text.strip()
                    price_str = price_elem.text.strip()
                    date_str = date_elem.text.strip() if date_elem else ""

                    # Preis bereinigen: deutsches Format "1.999 €" → "1999", "1.099,50 €" → "109950" → ignoriert Cent
                    price_str_clean = price_str.replace(".", "").replace(",", "")
                    clean_price = "".join(filter(str.isdigit, price_str_clean))
                    price = int(clean_price) if clean_price else 0

                    if db_min_price <= price <= db_max_price:
                        # Wichtige Negativ-Filter anwenden
                        t_lower = title.lower()
                        if any(exclude in t_lower for exclude in ["suche", "tausche", "karton", "verpackung", "defekt", "displayschaden", "hülle"]):
                            seen_ads.add(ad_id)
                            continue

                        link = "https://www.kleinanzeigen.de" + link_elem["href"]
                        new_deals.append({
                            "id": ad_id,
                            "title": title,
                            "price": price,
                            "date": date_str,
                            "link": link
                        })
                    seen_ads.add(ad_id)

                # Seen-Ads-Liste auf MAX_SEEN begrenzen, um Speicherleck zu vermeiden
                if len(seen_ads) > MAX_SEEN:
                    seen_ads_trimmed = set(list(seen_ads)[-MAX_SEEN:])
                    seen_ads.clear()
                    seen_ads.update(seen_ads_trimmed)

                with open(SEEN_ADS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(list(seen_ads), f)

            finally:
                browser.close()

    except Exception as e:
        logger.error(f"Beim Scrapen für '{db_query}': {e}")

    return new_deals
