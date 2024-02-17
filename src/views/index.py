import asyncio
import uuid

import asyncpg
from nicegui import app, ui

from .utils import show_menu


def install(db: asyncpg.Pool):
    @ui.page("/")
    async def index():
        def popup_thigmajig():
            dialog = ui.dialog()
            with dialog, ui.card():
                f = ui.input("Create New Folder", placeholder="Folder name")

                async def create_new_folder():
                    role = await db.fetch(
                        "SELECT roles FROM users WHERE session = $1",
                        str(app.storage.user.get("authenticator")),
                    )
                    if role[0]["roles"] != "admin":
                        ui.notify(
                            "You are NOT an Administrator. Please contact your administrator for creating new folders.",
                            type="negative",
                        )
                        return
                    await db.execute(
                        "INSERT INTO folders(name, accessers, id) VALUES($1, $2, $3)",
                        f.value,
                        [],
                        str(uuid.uuid4()),
                    )
                    ui.notify("Refreshing in 2 seconds", type="info")
                    await asyncio.sleep(2)
                    ui.open("/")

                ui.button("Submit", on_click=create_new_folder)
            return dialog.open

        left_drawer = (
            ui.drawer("left")
            .classes("items-center")
            .style("background-color: whitesmoke")
        )
        with ui.header(elevated=True).classes("items-center justify-between"):
            ui.button(on_click=await show_menu(left_drawer, db)).props(
                "flat color=white icon=menu"
            )
            ui.label("Folderistic - Listing")
            ui.button(on_click=popup_thigmajig()).props(
                "flat color=white icon=create_new_folder"
            )
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
        with ui.row(wrap=True).classes("items-start justify-center gap-10 m-4"):
            async with db.acquire() as d:
                if x := await db.fetch(
                    "SELECT roles FROM users WHERE session = $1",
                    str(app.storage.user.get("authenticator")),
                ):
                    if x[0]["roles"] == "admin":
                        x = await d.fetch("SELECT * FROM folders")
                    else:
                        x = await d.fetch(
                            "SELECT * FROM folders WHERE (SELECT username FROM users WHERE session = $1) = ANY(accessers);",
                            str(app.storage.user.get("autheticator")),
                        )
                for f in x:
                    with ui.column().classes("w-auto h-auto"):
                        with ui.button(on_click=lambda: ui.open(f"/{f['id']}")).classes(
                            "flex flex-col items-center justify-center"
                        ):
                            ui.icon("folder", size="md", color="darkorange")
                            ui.label(f'{f["name"]} (ID: {f["id"]})')
