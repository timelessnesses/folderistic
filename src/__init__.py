import asyncio
# import contextlib
# import typing
import uuid

import asyncpg
import fastapi
from dotenv import load_dotenv
from nicegui import app, ui

load_dotenv()
import logging
import os

from .middlewares import install_middlewares
from .views import install

db: asyncpg.Pool = None  # type: ignore


@app.on_startup
async def ls():
    g = logging.getLogger("folderistic.startup")
    global db
    db = await asyncpg.create_pool(host=os.getenv("FOLDERISTIC_HOST"), user=os.getenv("FOLDERISTIC_USER"), password=os.getenv("FOLDERISTIC_PASS"), database=os.getenv("FOLDERISTIC_DB"))  # type: ignore
    install(app, db)
    if db is None:
        raise Exception("pool is none?")
    g.info("Connected to database")
    print("hi")
    with open("./src/start.sql") as s:
        await db.execute(s.read())  # type: ignore
        g.info("Executed starter statements")


@app.on_shutdown
async def die():
    await db.close()


install_middlewares(app)

try:
    with open("./SECRET.uuid4") as fp:
        secret = fp.read()
except FileNotFoundError:
    secret = str(uuid.uuid4())
    with open("./SECRET.uuid4", "w") as fp:
        fp.write(secret)
print(secret)
app.add_middleware(middlewares.auth.AuthMiddleWare)
ui.run_with(
    app=fastapi.FastAPI(), title="Folderistic", dark=None, storage_secret=secret
)
