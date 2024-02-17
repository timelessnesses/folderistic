import asyncpg
import fastapi

from . import index, login


def install(app: fastapi.FastAPI, db: asyncpg.Pool):
    index.install(db)
    login.install(db)
