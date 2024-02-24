import asyncpg
import fastapi

from . import accessing_file, failed_auth, folder, index, login, about


def install(app: fastapi.FastAPI, db: asyncpg.Pool):
    index.install(db)
    login.install(db)
    failed_auth.install(db)
    folder.install(db)
    accessing_file.install(app, db)
    about.install(app, db)