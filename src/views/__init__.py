import asyncpg
import fastapi

from . import failed_auth, folder, index, login, accessing_file


def install(app: fastapi.FastAPI, db: asyncpg.Pool):
    index.install(db)
    login.install(db)
    failed_auth.install(db)
    folder.install(db)
    accessing_file.install(app, db)
