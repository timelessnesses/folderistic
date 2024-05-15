import asyncpg
import fastapi
import logfire

from . import about, accessing_file, failed_auth, folder, index, login


def install(app: fastapi.FastAPI, db: asyncpg.Pool):
    logfire.debug("Installing routes")
    index.install(db)
    login.install(db)
    failed_auth.install(db)
    folder.install(app, db)
    accessing_file.install(app, db)
    about.install(app, db)
    logfire.debug("Installed routes")