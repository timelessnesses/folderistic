import asyncio
import datetime
import os
import time
import typing

import asyncpg
import psutil
from nicegui import app, ui

from ..models import UserRecord

# ping = 0


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


async def db_ping(db: asyncpg.Pool):
    global ping
    async with db.acquire() as d:
        start = time.time()
        await d.fetch("SELECT 1;")
        stop = time.time()
    # ping = stop - start
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

            async def set_stuff():
                a.set_text(
                    f"Database Latency: {(await db_ping(db)) * 1000:.2f} milliseconds"
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
