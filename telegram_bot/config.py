import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

BACKEND_BASE_URL = os.getenv(
    "BACKEND_BASE_URL",
    "http://127.0.0.1:8080",
).rstrip("/")

PUBLIC_BASE_URL = os.getenv(
    "PUBLIC_BASE_URL",
    "https://176-12-76-67.sslip.io:8443",
).rstrip("/")

CHANNEL_USERNAME = os.getenv(
    "TELEGRAM_CHANNEL_USERNAME",
    "@vpn_ponchik",
)

if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN не найден в .env")