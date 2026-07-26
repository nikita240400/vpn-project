from __future__ import annotations
from backend.app.services.qrcode_service import generate_qr_base64

import httpx

from backend.app.core.config import (
    MARZBAN_BASE_URL,
    MARZBAN_PASSWORD,
    MARZBAN_USERNAME,
)


class MarzbanAPIError(Exception):
    pass


class MarzbanClient:
    def __init__(self) -> None:
        self.base_url = MARZBAN_BASE_URL
        self.username = MARZBAN_USERNAME
        self.password = MARZBAN_PASSWORD

        self._token: str | None = None

    def login(self) -> str:
        response = httpx.post(
            f"{self.base_url}/api/admin/token",
            data={
                "username": self.username,
                "password": self.password,
            },
            timeout=15,
        )

        response.raise_for_status()

        token = response.json()["access_token"]

        self._token = token

        return token

    def headers(self) -> dict[str, str]:
        if self._token is None:
            self.login()

        return {
            "Authorization": f"Bearer {self._token}"
        }

    def get_users(self):
        response = httpx.get(
            f"{self.base_url}/api/users",
            headers=self.headers(),
            timeout=20,
        )

        response.raise_for_status()

        return response.json()

    def create_user(self, payload: dict):
        response = httpx.post(
            f"{self.base_url}/api/user",
            headers=self.headers(),
            json=payload,
            timeout=20,
    )

        response.raise_for_status()

        result = response.json()

        result = response.json()

        link = result["links"][0]

        return {
            "username": result["username"],
             "link": link,
             "subscription_url": result["subscription_url"],
             "qr_code": generate_qr_base64(link),
        }


marzban_client = MarzbanClient()