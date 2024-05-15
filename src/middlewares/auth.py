import datetime

import asyncpg
import fastapi
import logfire
import starlette.middleware.base
import starlette.types
from nicegui import Client
from nicegui import app as napp


class AuthMiddleWare(starlette.middleware.base.BaseHTTPMiddleware):

    db: asyncpg.Pool

    def __init__(self, app: starlette.types.ASGIApp, database: asyncpg.Pool) -> None:
        super().__init__(app, None)
        self.db = database
        napp.on_disconnect(self.on_disconnect)

    async def dispatch(self, request: fastapi.Request, call_next) -> fastapi.Response:
        with logfire.span("Authentication Middleware Triggered"):    
            if not await self.logged_in():
                logfire.debug("User is not logged in.")
                if (
                    request.url.path in Client.page_routes.values()
                    and request.url.path not in ["/login", "/failed_auth", "/about"]
                ):
                    logfire.debug("Returning to failed_auth")
                    return fastapi.responses.RedirectResponse("/failed_auth")
            async with self.db.acquire() as d:
                logfire.debug("Changing the first_connected based on session")
                await d.execute(
                    "UPDATE users SET first_connected = $2 WHERE session = $1",
                    str(napp.storage.user.get("authenticator")),
                    datetime.datetime.now(),
                )
            logfire.info("Proceed to next request")
            return await call_next(request)

    async def on_disconnect(
        self, client: Client
    ):  # !!!: REMINDER: This does NOT work! See https://github.com/zauberzeug/nicegui/discussions/2662 for progress about this. I am not DRYing my code with `await client.disconnected()`
        # print(napp.storage.browser)
        # async with self.db.acquire() as d:
        #    await d.execute("UPDATE users SET last_connected = $2 WHERE session = $1", str(napp.storage.user.get("authenticator")), datetime.datetime.now())
        logfire.debug("Client disconnected (who?)")
        pass

    async def logged_in(self):
        # d: asyncpg.Connection
        tries = 0
        e = []
        global db
        logfire.debug("Tries to authenticate user based on the session ID'")
        while tries <= 5:
            logfire.debug(f"{tries=} Try")
            try:
                if (
                    len(
                        await self.db.fetch(
                            "SELECT * FROM users WHERE session = $1",
                            str(napp.storage.user.get("authenticator", None)),
                        )
                    )
                    == 0
                ):
                    logfire.debug("Session ID doesn't match at all. Resetting.")
                    napp.storage.user["authenticated"] = False
                    napp.storage.user["authenticator"] = None
                    return False
                return True
            except Exception as a:
                logfire.exception("Failed to verify. Trying again")
                tries += 1
                e.append(a)
        logfire.error("Cannot authenticate user")
        raise Exception("Unable to fetch data") from ExceptionGroup(
            "Errors while fetching data from database", e
        )
