import asyncio

# import contextlib
# import typing
import uuid

import asyncpg
import bcrypt
import fastapi
import nicegui.ui as ui
import starlette.middleware.base
from dotenv import load_dotenv
from nicegui import Client, app

load_dotenv()
import os


# @contextlib.asynccontextmanager
async def ls():
    global db
    db = await asyncpg.create_pool(host=os.getenv("FOLDERISTIC_HOST"), user=os.getenv("FOLDERISTIC_USER"), password=os.getenv("FOLDERISTIC_PASS"), database=os.getenv("FOLDERISTIC_DB"))  # type: ignore
    await db.execute(
        """
CREATE TABLE IF NOT EXISTS users(
    username TEXT,
    password TEXT,
    salt TEXT,
    session TEXT
)
                     """
    )
    await db.execute(
        """
CREATE TABLE IF NOT EXISTS authenticated(
    username TEXT,
    uuid TEXT
)
                     """
    )


async def die():
    await db.close()


app.on_startup(ls)
app.on_shutdown(die)

db: asyncpg.Pool = None  # type: ignore
fa = fastapi.FastAPI(docs_url=None, redoc_url=None)


class AuthMiddleWare(starlette.middleware.base.BaseHTTPMiddleware):
    async def dispatch(self, request: fastapi.Request, call_next) -> fastapi.Response:
        print(await self.logged_in())
        if not await self.logged_in():
            print("they are not logged in")
            if (
                request.url.path in Client.page_routes.values()
                and request.url.path not in ["/login"]
            ):
                print("redirect now!!!")
                return fastapi.responses.RedirectResponse("/login")
        return await call_next(request)

    async def logged_in(self):
        # d: asyncpg.Connection
        async with db.acquire() as d:
            if app.storage.user.get("authenticated", False):
                if (
                    len(
                        await d.fetch(
                            "SELECT * FROM authenticated WHERE uuid = $1",
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


def show_menu(l: ui.drawer):
    async def logout():
        async with db.acquire() as d:
            name = await d.fetch(
                "SELECT username FROM authenticated WHERE uuid = $1",
                str(app.storage.user.get("authenticator", "")),
            )
            if len(name) != 0:
                ui.notify(f"See you again! {name[0]['username']}")
                await asyncio.sleep(3)
        app.storage.user["authenticated"] = False
        app.storage.user["authenticator"] = None
        ui.open("/login")

    with l:
        ui.label("📂 Folderistic").style("font-size: 25px")
        if app.storage.user["authenticated"]:
            ui.button("Logout", on_click=logout).classes("red")
        else:
            ui.button("Login", on_click=lambda: ui.open("/login"))

    def h():
        l.toggle()

    return h


@ui.page("/")
async def index():
    left_drawer = (
        ui.drawer("left").classes("items-center").style("background-color: whitesmoke")
    )
    with ui.header(elevated=True).classes("items-center justify-between"):
        ui.button(on_click=show_menu(left_drawer)).props("flat color=white icon=menu")
        ui.label("Folderistic - Listing")
        ui.label()
        # d: asyncpg.Connection
        async with db.acquire() as d:
            name = await d.fetch(
                "SELECT username FROM authenticated WHERE uuid = $1",
                str(app.storage.user.get("authenticator", "")),
            )
            if len(name) == 0:
                return
        ui.notify(f"Welcome {name[0]['username']}!")
        # ui.separator()
    with ui.row(wrap=True).classes('items-start justify-center gap-10 m-4'):
        for i in range(100):
            with ui.column().classes("w-auto h-auto"):
                with ui.card().classes("flex flex-col items-center justify-center"):
                    ui.icon("folder", size="md", color="darkorange")
                    ui.label("testicles")


@ui.page("/login")
async def login():
    async def try_login():
        # print("yay!!")
        p = password.value
        u = username.value

        ui.notify("Currently going through database.", close_button=True, type="info")
        # d: asyncpg.Connection
        async with db.acquire() as d:
            if (
                len(
                    x := await d.fetch(
                        "SELECT salt, password FROM users WHERE username = $1", u
                    )
                )
                == 0
            ):
                ui.notify("Failed to authenticate: User is NOT found", type="negative")
                return
            salt: tuple[str, str] = x[0]  # type: ignore
            print(salt)

        salted_password = bcrypt.hashpw(p.encode(), bytes.fromhex(salt["salt"]))  # type: ignore
        if salted_password != bytes.fromhex(salt["password"]):  # type: ignore
            ui.notify(
                "Failed to authenticate: Password is NOT correct.", type="negative"
            )
            return
        ui.notify("Welcome to Folderistic!", type="positive")
        id = uuid.uuid4()
        app.storage.user["authenticated"] = True
        app.storage.user["authenticator"] = id
        # d: asyncpg.Connection
        async with db.acquire() as d:
            await d.execute(
                "INSERT INTO authenticated(username, uuid) VALUES ($1, $2)", u, str(id)
            )
        ui.open("/")

    if app.storage.user.get("authenticated", False):
        # d: asyncpg.Connection
        async with db.acquire() as d:
            if app.storage.user.get("authenticated", False):
                if (
                    len(
                        await d.fetch(
                            "SELECT * FROM authenticated WHERE uuid = $1",
                            app.storage.user.get("authenticator", None),
                        )
                    )
                    != 0
                ):
                    ui.open("/")
                    return
    left_drawer = (
        ui.drawer("left").classes("items-center").style("background-color: whitesmoke")
    )
    with ui.header(elevated=True).classes("items-center justify-between"):
        ui.button(on_click=show_menu(left_drawer)).props("flat color=white icon=menu")
        ui.label("Folderistic - Login")
        ui.label()
    with ui.card().classes("absolute-center"):
        username = ui.input("Username").on("keydown.enter", try_login)
        password = ui.input("Password", password=True, password_toggle_button=True).on(
            "keydown.enter", try_login
        )
        ui.button("Log in", on_click=try_login)
        ui.button(
            "Register",
            on_click=lambda: ui.notify(
                "Please ask system administrator to add you manually. Thanks!",
                close_button=True,
                type="warning",
            ),
        )
    return None


app.add_middleware(AuthMiddleWare)

ui.run_with(fa, title="Folderistic", dark=None, storage_secret="BALLER")
