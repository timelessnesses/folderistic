import uuid

import asyncpg
import bcrypt
from nicegui import app, ui

from .utils import show_menu


def install(db: asyncpg.Pool):
    @ui.page("/login")
    async def login():
        async def try_login():
            p = password.value
            u = username.value

            ui.notify(
                "Currently going through database.", close_button=True, type="info"
            )
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
                    ui.notify(
                        "Failed to authenticate: User is NOT found", type="negative"
                    )
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
            ui.drawer("left")
            .classes("items-center")
            .style("background-color: whitesmoke")
        )
        with ui.header(elevated=True).classes("items-center justify-between"):
            ui.button(on_click=await show_menu(left_drawer, db)).props(
                "flat color=white icon=menu"
            )
            ui.label("Folderistic - Login")
            ui.label()
        with ui.card().classes("absolute-center"):
            username = ui.input("Username").on("keydown.enter", try_login)
            password = ui.input(
                "Password", password=True, password_toggle_button=True
            ).on("keydown.enter", try_login)
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
