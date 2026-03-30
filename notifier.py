import requests
import time
import logging

logger = logging.getLogger(__name__)

MAX_RETRIES = 3

def send_telegram_message(bot_token, chat_id, message):
    if bot_token == "HIER_TOKEN_EINTRAGEN" or chat_id == "HIER_CHAT_ID_EINTRAGEN":
        logger.warning("Telegram Bot nicht konfiguriert. Bitte .env anpassen.")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            if attempt < MAX_RETRIES:
                wait = 2 ** attempt  # 2s, 4s
                logger.warning(f"Telegram-Versuch {attempt} fehlgeschlagen, erneuter Versuch in {wait}s: {e}")
                time.sleep(wait)
            else:
                logger.error(f"Telegram-Nachricht konnte nach {MAX_RETRIES} Versuchen nicht gesendet werden: {e}")
                return False
