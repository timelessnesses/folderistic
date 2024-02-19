import asyncio

from dotenv import load_dotenv

load_dotenv()
import os

import asyncpg
import fastapi
import starlette.middleware.base
import starlette.types
from nicegui import Client, app

# db: asyncpg.Pool

db = None  # type: ignore


class AuthMiddleWare(starlette.middleware.base.BaseHTTPMiddleware):
    initialized_db = False
    db: asyncpg.Connection

    async def get_db(self):
        global db
        if not self.initialized_db or db is None:
            self.db = await asyncpg.create_pool(host=os.getenv("FOLDERISTIC_HOST"), user=os.getenv("FOLDERISTIC_USER"), password=os.getenv("FOLDERISTIC_PASS"), database=os.getenv("FOLDERISTIC_DB"))  # type: ignore
            db = self.db
        self.initialized_db = True

    async def dispatch(self, request: fastapi.Request, call_next) -> fastapi.Response:
        await self.get_db()
        if not await self.logged_in():
            if (
                request.url.path in Client.page_routes.values()
                and request.url.path not in ["/login", "/failed_auth"]
            ):
                return fastapi.responses.RedirectResponse("/failed_auth")
        return await call_next(request)

    async def logged_in(self):
        # d: asyncpg.Connection
        tries = 0
        e = None
        global db
        x = db or self.db
        while tries <= 5:
            try:
                if app.storage.user.get("authenticated", False):
                    if (
                        len(
                            await self.db.fetch(
                                "SELECT * FROM users WHERE session = $1",
                                str(app.storage.user.get("authenticator", None)),
                            )
                        )
                        == 0
                    ):
                        app.storage.user["authenticated"] = False
                        app.storage.user["authenticated"] = None
                        return False
                else:
                    return False
                return True
            except Exception as a:
                tries += 1
                e = a
                print(a)
        raise Exception("Unable to fetch data") from e
