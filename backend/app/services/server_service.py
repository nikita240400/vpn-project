from sqlalchemy.orm import Session

from backend.app.models.server import Server


class ServerService:
    def get_all(self, db: Session) -> list[Server]:
        return (
            db.query(Server)
            .order_by(Server.priority.asc(), Server.id.asc())
            .all()
        )

    def create(
        self,
        db: Session,
        data: dict,
    ) -> Server:
        server = Server(**data)

        db.add(server)

        try:
            db.commit()
            db.refresh(server)
        except Exception:
            db.rollback()
            raise

        return server

    def update(
        self,
        db: Session,
        server: Server,
        data: dict,
    ) -> Server:
        for field, value in data.items():
            setattr(server, field, value)

        try:
            db.commit()
            db.refresh(server)
        except Exception:
            db.rollback()
            raise

        return server

    def delete(
        self,
        db: Session,
        server: Server,
    ) -> None:
        db.delete(server)

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise


server_service = ServerService()