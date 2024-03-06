import asyncio
import datetime
import time
import requests
import subprocess
import typing
from dotenv import load_dotenv
load_dotenv()
import os

import asyncpg
import psutil
from nicegui import app, ui, Client

from ..models import UserRecord

def get_commit_id():
    try:
        if git := subprocess.check_output("git rev-parse HEAD", shell=True):
            return git.decode()
    except (subprocess.CalledProcessError, FileNotFoundError):
        if env := os.getenv("FOLDERISTIC_COMMIT_ID"):
            return env
    return "Undetectable"

COMMIT_ID = get_commit_id().replace("\n", "").replace("\r", "")
DOCKER = bool(os.getenv("FOLDERISTIC_DOCKER", 0))
IS_UP_TO_DATE: bool = requests.get("https://api.github.com/repos/timelessnesses/folderistic/commits/master").json()["sha"] == COMMIT_ID

class CustomButtonBuilder:
    """
    A custom button builder to be used in functions.
    """

    on_click: typing.Callable[..., typing.Any]
    "On click function"

    prop: str
    "Props"

    def __init__(self, on_click: typing.Callable[..., typing.Any]) -> None:
        self.on_click = on_click

    def props(self, props: str) -> typing.Self:
        "Apply props to button"
        self.prop = props
        return self


start = datetime.datetime.now()

is_pinging = False

async def db_ping(db: asyncpg.Pool):
    global is_pinging
    async with db.acquire() as d:
        is_pinging = True
        start = time.time()
        await d.fetch("SELECT 1;")
        stop = time.time()
    is_pinging = False
    return stop - start


def cpu():
    return round(psutil.cpu_percent(), 2)


def disk():
    return round(psutil.disk_usage("/").percent, 2)


async def show_menu(l: ui.drawer, db: asyncpg.Pool | None):
    """Showing menu in header

    Args:
        l (ui.drawer): A drawer
        db (asyncpg.Pool | None, optional): Database
    """
    if db is not None:

        async def logout():
            async with db.acquire() as d:
                name = await d.fetch(
                    "SELECT username FROM users WHERE session = $1",
                    str(app.storage.user.get("authenticator", "")),
                    record_class=UserRecord,
                )
                if len(name) != 0:
                    ui.notify(f"See you again! {name[0].username}")
                    await asyncio.sleep(3)
            app.storage.user["authenticated"] = False
            app.storage.user["authenticator"] = None
            ui.open("/login")

    else:

        async def logout(): ...

    with l:
        ui.link("📂 Folderistic").style("font-size: 25px").on(
            "click", lambda: ui.open("/")
        )
        if app.storage.user.get("authenticated", None) and db is not None:

            x = await db.fetch(
                "SELECT username, roles FROM users WHERE session = $1",
                str(app.storage.user.get("authenticator")),
                record_class=UserRecord,
            )
            username = x[0].username
            role: str = x[0].roles
            ui.label(f"User: {username} Role: {role.capitalize()}").style(
                "font-size: 15px"
            )
            
            if role == "admin":
                def process_broadcast(i: ui.textarea | ui.input, admin: str):
                    v = i.value
                    def x():
                        ui.notify("Sending broadcasts.", type="ongoing", timeout=2000)
                        for client in Client.instances.values():
                            with client:
                                with ui.dialog(value=True), ui.card():
                                    ui.markdown(f"""
                                                # Broadcasting
                                                Administrator {admin} has sent you a message<br>
                                                {v}
                                                """)
                        ui.notify("Sent broadcasts!", type="positive")
                    x()   
                async def broadcasting():
                    with ui.dialog(value=True), ui.card():
                        ui.label("Please input your messages that you wanted to broadcast.")
                        a = ui.input('Hello world!').props('type=textarea clearable')
                        ui.button("Submit", on_click=lambda: process_broadcast(a, username))
                ui.button("Broadcast Message", on_click=broadcasting, color="green")
            async def set_stuff():
                a.set_text(
                    f"Database Latency: {await db_ping(db) * 1000:.2f} milliseconds" # type: ignore
                )
                b.set_text(f"CPU: {cpu()}%")
                c.set_text(f"Disk: {disk()}%")
                d.set_text(
                    f"Has been running for: {str(datetime.datetime.now() - start).split('.')[0]}"
                )
                e.set_text(f"RAM: {round(psutil.virtual_memory().percent,2)}%")

            a = ui.label("Database Latency: Unmeasured")
            b = ui.label("CPU: Unmeasured")
            c = ui.label("Disk: Unmeasured")
            e = ui.label("RAM: Unmeasured")
            d = ui.label("Has been running for: Not Found")
            ui.timer(1, set_stuff)
            ui.button("Logout", on_click=logout, color="red")
        else:
            ui.button("Login", on_click=lambda: ui.open("/login"))
        ui.button("About", on_click=lambda: ui.open("/about"))
        ui.link(f"Commit ID: {COMMIT_ID[:7]} {'' if IS_UP_TO_DATE else '⚠️ New update available.'}", f"https://github.com/timelessnesses/folderistic/commit/{COMMIT_ID}")
        ui.label(f"Dockerized: {DOCKER}")

    def h():
        l.toggle()

    return h


async def show_header(
    db: asyncpg.Pool | None,
    header_name: str,
    buttons: list[CustomButtonBuilder] | None = None,
):
    """A function that shows header

    Args:
        db (asyncpg.Pool | None, optional): Database
        header_name (str): Text to display in the header
        buttons (list[CustomButtonBuilder] | None, optional): Buttons to display on one side of the header.
    """
    left_drawer = (
        ui.drawer("left").classes("items-center").style("background-color: whitesmoke")
    )
    with ui.header(elevated=True).classes("flex items-center justify-between"):
        ui.button(on_click=await show_menu(left_drawer, db)).props(
            "flat color=white icon=menu"
        )
        ui.label(f"Folderistic - {header_name}").classes("mx-auto")
        if buttons:
            for button in buttons:
                ui.button(on_click=button.on_click).props(button.prop)
        else:
            ui.label()


async def say_hi(db: asyncpg.Pool):
    """Function that says hi to user

    Args:
        db (asyncpg.Pool): Database
    """
    async with db.acquire() as d:
        name: list[UserRecord] = await d.fetch(
            "SELECT username FROM users WHERE session = $1",
            str(app.storage.user.get("authenticator", "")),
            record_class=UserRecord,
        )
        if len(name) == 0:
            return
    ui.notify(f"Welcome {name[0].username}!")
