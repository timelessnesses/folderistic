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


class AuthMiddleWare(starlette.middleware.base.BaseHTTPMiddleware):
    initialized_db = False
    db: asyncpg.Connection
    async def get_db(self):
        if not self.initialized_db:
            self.db = await asyncpg.connect(host=os.getenv("FOLDERISTIC_HOST"), user=os.getenv("FOLDERISTIC_USER"), password=os.getenv("FOLDERISTIC_PASS"), database=os.getenv("FOLDERISTIC_DB"))  # type: ignore
        self.initialized_db = True

    async def dispatch(self, request: fastapi.Request, call_next) -> fastapi.Response:
        await self.get_db()
        if not await self.logged_in():
            if (
                request.url.path in Client.page_routes.values()
                and request.url.path not in ["/login"]
            ):
                return fastapi.responses.RedirectResponse("/login")
        return await call_next(request)

    async def logged_in(self):
        # d: asyncpg.Connection
        tries = 0
        e = None
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
