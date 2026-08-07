import httpx

from telegram_bot.config import BACKEND_BASE_URL


class BackendAPIError(Exception):
    pass


async def activate_trial(
    telegram_id: int,
    username: str | None,
) -> dict:
    payload = {
        "telegram_id": str(telegram_id),
        "username": username,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BACKEND_BASE_URL}/telegram/trial/activate",
                json=payload,
            )

    except httpx.RequestError as error:
        raise BackendAPIError(
            "Backend недоступен"
        ) from error

    if response.is_error:
        try:
            detail = response.json().get("detail")
        except ValueError:
            detail = None

        raise BackendAPIError(
            detail or f"Backend вернул ошибку {response.status_code}"
        )

    return response.json()

async def get_account(
    telegram_id: int,
    username: str | None,
) -> dict:
    payload = {
        "telegram_id": str(telegram_id),
        "username": username,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BACKEND_BASE_URL}/telegram/account",
                json=payload,
            )

    except httpx.RequestError as error:
        raise BackendAPIError(
            "Backend недоступен"
        ) from error

    if response.is_error:
        try:
            detail = response.json().get("detail")
        except ValueError:
            detail = None

        raise BackendAPIError(
            detail or f"Backend вернул ошибку {response.status_code}"
        )

    return response.json()

async def get_plans() -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BACKEND_BASE_URL}/plans",
            )

    except httpx.RequestError as error:
        raise BackendAPIError(
            "Backend недоступен"
        ) from error

    if response.is_error:
        try:
            detail = response.json().get("detail")
        except ValueError:
            detail = None

        raise BackendAPIError(
            detail or f"Backend вернул ошибку {response.status_code}"
        )

    return response.json()

async def sync_telegram_user(
    telegram_id: int,
    username: str | None,
) -> dict:
    payload = {
        "telegram_id": str(telegram_id),
        "username": username,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BACKEND_BASE_URL}/telegram/users/sync",
                json=payload,
            )

    except httpx.RequestError as error:
        raise BackendAPIError(
            "Backend недоступен"
        ) from error

    if response.is_error:
        try:
            detail = response.json().get("detail")
        except ValueError:
            detail = None

        raise BackendAPIError(
            detail or f"Backend вернул ошибку {response.status_code}"
        )

    return response.json()