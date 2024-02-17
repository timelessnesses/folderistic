import asyncpg
import fastapi

from . import index, login, folder


def install(app: fastapi.FastAPI, db: asyncpg.Pool):
    index.install(db)
    login.install(db)
    folder.install(db)