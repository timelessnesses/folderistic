import asyncpg
import fastapi

from . import failed_auth, folder, index, login


def install(_: fastapi.FastAPI, db: asyncpg.Pool):
    index.install(db)
    login.install(db)
    failed_auth.install(db)
    folder.install(db)
