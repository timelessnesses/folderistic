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
import time
load_dotenv()
import os

@app.on_startup
async def ls():
    global db
    db = await asyncpg.create_pool(host=os.getenv("FOLDERISTIC_HOST"), user=os.getenv("FOLDERISTIC_USER"), password=os.getenv("FOLDERISTIC_PASS"), database=os.getenv("FOLDERISTIC_DB"))  # type: ignore
    with open("./src/start.sql") as s:
        await db.execute(s.read())

@app.on_shutdown
async def die():
    await db.close()


db: asyncpg.Pool = None  # type: ignore
fa = fastapi.FastAPI(docs_url=None, redoc_url=None)


class AuthMiddleWare(starlette.middleware.base.BaseHTTPMiddleware):
    async def dispatch(self, request: fastapi.Request, call_next) -> fastapi.Response:
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
        while tries <= 5:
            try:
                async with db.acquire() as d:
                    if app.storage.user.get("authenticated", False):
                        if (
                            len(
                                await d.fetch(
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
            except:
                tries += 1
                await asyncio.sleep(1)
        raise Exception("Unable to fetch data")


async def show_menu(l: ui.drawer):
    async def logout():
        async with db.acquire() as d:
            name = await d.fetch(
                "SELECT username FROM users WHERE session = $1",
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
        if app.storage.user.get("authenticated", None):
            x = await db.fetch('SELECT username, roles FROM users WHERE session = $1', str(app.storage.user.get('authenticator')))
            username = x[0]['username']
            role: str = x[0]["roles"]
            ui.label(f"User: {username} Role: {role.capitalize()}").style("font-size: 15px")
            ui.button("Logout", on_click=logout).classes("red")
        else:
            ui.button("Login", on_click=lambda: ui.open("/login"))

    def h():
        l.toggle()

    return h


@ui.page("/")
async def index():
    def popup_thigmajig():
        dialog = ui.dialog()
        with dialog, ui.card():
            f = ui.input("Create New Folder", placeholder="Folder name")
            async def create_new_folder():
                role = await db.fetch("SELECT roles FROM users WHERE session = $1", str(app.storage.user.get("authenticator")))
                if role[0]["roles"] != "admin":
                    ui.notify("You are NOT an Administrator. Please contact your administrator for creating new folders.", type="negative")
                    return
                await db.execute("INSERT INTO folders(name, accessers, id) VALUES($1, $2, $3)", f.value, [], str(uuid.uuid4()))
                ui.notify("Refreshing in 2 seconds", type="info")
                await asyncio.sleep(2)
                ui.open("/")
            ui.button("Submit", on_click=create_new_folder)
        return dialog.open
    left_drawer = (
        ui.drawer("left").classes("items-center").style("background-color: whitesmoke")
    )
    with ui.header(elevated=True).classes("items-center justify-between"):
        ui.button(on_click=await show_menu(left_drawer)).props("flat color=white icon=menu")
        ui.label("Folderistic - Listing")
        ui.button(on_click=popup_thigmajig()).props("flat color=white icon=create_new_folder")
        # d: asyncpg.Connection
        async with db.acquire() as d:
            name = await d.fetch(
                "SELECT username FROM users WHERE session = $1",
                str(app.storage.user.get("authenticator", "")),
            )
            if len(name) == 0:
                return
        ui.notify(f"Welcome {name[0]['username']}!")
        # ui.separator()
    with ui.row(wrap=True).classes('items-start justify-center gap-10 m-4'):
        async with db.acquire() as d:
            if (x := await db.fetch("SELECT roles FROM users WHERE session = $1", str(app.storage.user.get("authenticator")))):
                if x[0]["roles"] == "admin":
                    x = await d.fetch("SELECT * FROM folders")
                else:
                    x = await d.fetch("SELECT * FROM folders WHERE (SELECT username FROM users WHERE session = $1) = ANY(accessers);", str(app.storage.user.get("autheticator")))
            for f in x:
                with ui.column().classes("w-auto h-auto"):
                    with ui.button(on_click=lambda: ui.open(f"/{f['id']}")).classes("flex flex-col items-center justify-center"):
                        ui.icon("folder", size="md", color="darkorange")
                        ui.label(f'{f["name"]} (ID: {f["id"]})')


@ui.page("/login")
async def login():
    async def try_login():
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
            salt = x[0]  # type: ignore

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
                "UPDATE users SET session = $2 WHERE username = $1", u, str(id)
            )
        ui.open("/")

    if app.storage.user.get("authenticated", False):
        # d: asyncpg.Connection
        async with db.acquire() as d:
            if app.storage.user.get("authenticated", False):
                if (
                    len(
                        await d.fetch(
                            "SELECT * FROM users WHERE session = $1",
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
        ui.button(on_click=await show_menu(left_drawer)).props("flat color=white icon=menu")
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

try:
    with open("./SECRET.uuid4") as fp:
        secret = fp.read()
except FileNotFoundError:
    secret = str(uuid.uuid4())
    with open("./SECRET.uuid4", "w") as fp:
        fp.write(secret)
ui.run_with(fa, title="Folderistic", dark=None, storage_secret=secret)
