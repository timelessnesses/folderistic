import asyncio

from dotenv import load_dotenv

load_dotenv()
import os

import asyncpg
import fastapi
import starlette.middleware.base
import starlette.types
from nicegui import Client, app


class AuthMiddleWare(starlette.middleware.base.BaseHTTPMiddleware):

    db: asyncpg.Pool

    def __init__(self, app: starlette.types.ASGIApp, database: asyncpg.Pool) -> None:
        super().__init__(app, None)
        self.db = database

    async def dispatch(self, request: fastapi.Request, call_next) -> fastapi.Response:
        if not await self.logged_in():
            if (
                request.url.path in Client.page_routes.values()
                and request.url.path not in ["/login", "/failed_auth", "/about"]
            ):
                return fastapi.responses.RedirectResponse("/failed_auth")
        return await call_next(request)

    async def logged_in(self):
        # d: asyncpg.Connection
        tries = 0
        e = None
        global db
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
