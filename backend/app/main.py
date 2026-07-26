from fastapi import FastAPI

from backend.app import models  # noqa: F401
from backend.app.api.routes import router
from backend.app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="VPN SaaS",
    version="0.1.0",
)

app.include_router(router)
