import asyncpg
import fastapi
import starlette.middleware.base
import starlette.types
from nicegui import Client, app as napp
import datetime

class AuthMiddleWare(starlette.middleware.base.BaseHTTPMiddleware):

    db: asyncpg.Pool

    def __init__(self, app: starlette.types.ASGIApp, database: asyncpg.Pool) -> None:
        super().__init__(app, None)
        self.db = database
        napp.on_disconnect(self.on_disconnect)

    async def dispatch(self, request: fastapi.Request, call_next) -> fastapi.Response:
        if not await self.logged_in():
            if (
                request.url.path in Client.page_routes.values()
                and request.url.path not in ["/login", "/failed_auth", "/about"]
            ):
                return fastapi.responses.RedirectResponse("/failed_auth")
        async with self.db.acquire() as d:
            await d.execute("UPDATE users SET first_connected = $2 WHERE session = $1", str(napp.storage.user.get("authenticator")), datetime.datetime.now())
        return await call_next(request)
    
    async def on_disconnect(self, client: Client):
        print(napp.storage.browser)
        async with self.db.acquire() as d:
            await d.execute("UPDATE users SET last_connected = $2 WHERE session = $1", str(napp.storage.user.get("authenticator")), datetime.datetime.now())

    async def logged_in(self):
        # d: asyncpg.Connection
        tries = 0
        e = []
        global db
        while tries <= 5:
            try:
                if napp.storage.user.get("authenticated", False):
                    if (
                        len(
                            await self.db.fetch(
                                "SELECT * FROM users WHERE session = $1",
                                str(napp.storage.user.get("authenticator", None)),
                            )
                        )
                        == 0
                    ):
                        napp.storage.user["authenticated"] = False
                        napp.storage.user["authenticated"] = None
                        return False
                else:
                    return False
                return True
            except Exception as a:
                tries += 1
                e.append(a)
        raise Exception("Unable to fetch data") from ExceptionGroup("Errors while fetching data from database", e)
