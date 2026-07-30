from __future__ import annotations

import httpx

from backend.app.core.config import (
    MARZBAN_BASE_URL,
    MARZBAN_PASSWORD,
    MARZBAN_USERNAME,
)
from backend.app.services.qrcode_service import generate_qr_base64


class MarzbanAPIError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class MarzbanClient:
    def __init__(
        self,
        base_url: str = MARZBAN_BASE_URL,
        username: str = MARZBAN_USERNAME,
        password: str = MARZBAN_PASSWORD,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self._token: str | None = None

    def login(self) -> str:
        try:
            response = httpx.post(
                f"{self.base_url}/api/admin/token",
                data={
                    "username": self.username,
                    "password": self.password,
                },
                timeout=15,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise MarzbanAPIError(
                f"Ошибка авторизации Marzban: HTTP "
                f"{error.response.status_code}"
            ) from error
        except httpx.RequestError as error:
            raise MarzbanAPIError(
                f"Нет соединения с Marzban: {error}"
            ) from error

        token = response.json().get("access_token")

        if not token:
            raise MarzbanAPIError(
                "Marzban не вернул access token"
            )

        self._token = token
        return token

    def headers(self) -> dict[str, str]:
        if self._token is None:
            self.login()

        return {
            "Authorization": f"Bearer {self._token}",
        }

    def get_users(self) -> dict:
        try:
            response = httpx.get(
                f"{self.base_url}/api/users",
                headers=self.headers(),
                timeout=20,
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise MarzbanAPIError(
                f"Не удалось получить пользователей: {error}"
            ) from error

        return response.json()

    def create_user(self, payload: dict) -> dict:
        try:
            response = httpx.post(
                f"{self.base_url}/api/user",
                headers=self.headers(),
                json=payload,
                timeout=20,
            )
            response.raise_for_status()

        except httpx.HTTPStatusError as error:
            raise MarzbanAPIError(
                message=(
                    f"Не удалось создать пользователя: HTTP "
                    f"{error.response.status_code} — "
                    f"{error.response.text}"
                ),
                status_code=error.response.status_code,
                response_body=error.response.text,
            ) from error

        except httpx.RequestError as error:
            raise MarzbanAPIError(
                f"Нет соединения с Marzban: {error}"
            ) from error

        result = response.json()

        links = result.get("links") or []

        if not links:
            raise MarzbanAPIError(
                message=(
                    "Marzban создал пользователя, "
                    "но не вернул VLESS-ссылку"
                ),
                response_body=response.text,
            )

        link = links[0]

        return {
            "username": result["username"],
            "vpn_uuid": result["proxies"]["vless"]["id"],
            "link": link,
            "subscription_url": result["subscription_url"],
            "expire": result["expire"],
            "data_limit": result.get("data_limit") or 0,
            "status": result["status"],
            "qr_code": generate_qr_base64(link),
        }

    def modify_user(
        self,
        username: str,
        payload: dict,
    ) -> dict:
        try:
            response = httpx.put(
                f"{self.base_url}/api/user/{username}",
                headers=self.headers(),
                json=payload,
                timeout=20,
            )
            response.raise_for_status()

        except httpx.HTTPStatusError as error:
            raise MarzbanAPIError(
                f"Не удалось изменить пользователя {username}: "
                f"HTTP {error.response.status_code} — "
                f"{error.response.text}"
            ) from error

        except httpx.RequestError as error:
            raise MarzbanAPIError(
                f"Нет соединения с Marzban: {error}"
            ) from error

        return response.json()


    def delete_user(self, username: str) -> None:
        try:
            response = httpx.delete(
                f"{self.base_url}/api/user/{username}",
                headers=self.headers(),
                timeout=20,
            )
            response.raise_for_status()

        except httpx.HTTPStatusError as error:
            raise MarzbanAPIError(
                f"Не удалось удалить пользователя "
                f"{username}: HTTP {error.response.status_code}"
            ) from error

        except httpx.RequestError as error:
            raise MarzbanAPIError(
                f"Нет соединения с Marzban: {error}"
            ) from error


marzban_client = MarzbanClient()