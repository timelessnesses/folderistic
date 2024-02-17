import asyncio

import asyncpg
from nicegui import app, ui
import typing
from ..models import UserRecord

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

async def show_menu(l: ui.drawer, db: asyncpg.Pool):
    """Showing menu in header

    Args:
        l (ui.drawer): A drawer
        db (asyncpg.Pool): Database
    """
    async def logout():
        async with db.acquire() as d:
            name = await d.fetch(
                "SELECT username FROM users WHERE session = $1",
                str(app.storage.user.get("authenticator", "")),
                record_class=UserRecord
            )
            if len(name) != 0:
                ui.notify(f"See you again! {name[0].username}")
                await asyncio.sleep(3)
        app.storage.user["authenticated"] = False
        app.storage.user["authenticator"] = None
        ui.open("/login")

    with l:
        ui.label("📂 Folderistic").style("font-size: 25px")
        if app.storage.user.get("authenticated", None):
            x = await db.fetch(
                "SELECT username, roles FROM users WHERE session = $1",
                str(app.storage.user.get("authenticator")),
                record_class=UserRecord
            )
            username = x[0].username
            role: str = x[0].roles
            ui.label(f"User: {username} Role: {role.capitalize()}").style(
                "font-size: 15px"
            )
            ui.button("Logout", on_click=logout).classes("red")
        else:
            ui.button("Login", on_click=lambda: ui.open("/login"))

    def h():
        l.toggle()

    return h

async def show_header(db: asyncpg.Pool, header_name: str,buttons: list[CustomButtonBuilder] | None = None):
    """A function that shows header

    Args:
        db (asyncpg.Pool): Database
        buttons (list[CustomButtonBuilder] | None, optional): Buttons with included props if you wish to add any. Defaults to None.
    """
    left_drawer = (
            ui.drawer("left")
            .classes("items-center")
            .style("background-color: whitesmoke")
        )
    with ui.header(elevated=True).classes("items-center justify-between"):
        ui.button(on_click=await show_menu(left_drawer, db)).props(
            "flat color=white icon=menu"
        )
        ui.label(f"Folderistic - {header_name}")
        if buttons is not None:
            for x in buttons:
                ui.button(on_click=x.on_click).props(x.prop)
        else:
            ui.label()
        # d: asyncpg.Connection
        async with db.acquire() as d:
            name: list[UserRecord] = await d.fetch(
                "SELECT username FROM users WHERE session = $1",
                str(app.storage.user.get("authenticator", "")),
                record_class=UserRecord
            )
            if len(name) == 0:
                return
        ui.notify(f"Welcome {name[0].username}!")