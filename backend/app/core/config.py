import os

from dotenv import load_dotenv

load_dotenv(".env")


def get_required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"{name} is not configured. Add it to the .env file."
        )

    return value


DATABASE_URL = get_required_env("DATABASE_URL")

MARZBAN_BASE_URL = get_required_env("MARZBAN_BASE_URL").rstrip("/")
MARZBAN_USERNAME = get_required_env("MARZBAN_USERNAME")
MARZBAN_PASSWORD = get_required_env("MARZBAN_PASSWORD")
