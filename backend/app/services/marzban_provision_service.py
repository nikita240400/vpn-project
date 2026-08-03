from backend.app.models.server import Server
from backend.app.services.marzban import (
    MarzbanAPIError,
    MarzbanClient,
)


class MarzbanProvisionService:
    """Works with Marzban servers."""

    def create_user(
        self,
        server: Server,
        payload: dict,
    ) -> tuple[MarzbanClient, dict]:
        marzban = MarzbanClient(
            base_url=server.marzban_base_url,
        )

        try:
            result = marzban.create_user(payload)
        except MarzbanAPIError as error:
            if error.status_code == 409:
                raise ValueError(
                    "User already exists in Marzban "
                    f"on server {server.id}, but the "
                    "subscription is missing in the "
                    "backend database"
                ) from error

            raise

        return marzban, result

    def rollback_created_users(
        self,
        created_users: list[tuple[MarzbanClient, str]],
    ) -> None:
        for marzban, username in reversed(created_users):
            try:
                marzban.delete_user(username)
            except MarzbanAPIError:
                pass


marzban_provision_service = MarzbanProvisionService()
