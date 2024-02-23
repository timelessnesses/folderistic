import asyncio
import uuid

import asyncpg
from nicegui import app, ui

from ..models import FolderRecord, UserRecord
from .utils import CustomButtonBuilder, say_hi, show_header


def install(db: asyncpg.Pool):
    @ui.page("/")
    async def index():
        def popup_thigmajig():
            dialog = ui.dialog()
            with dialog, ui.card():
                f = ui.input("Create New Folder", placeholder="Folder name")

                async def create_new_folder():
                    role = await db.fetch(
                        "SELECT roles, username FROM users WHERE session = $1",
                        str(app.storage.user.get("authenticator")),
                        record_class=UserRecord,
                    )
                    if role[0].roles not in ["admin", "uploaders"]:
                        ui.notify(
                            "You are NOT an Administrator. Please contact your administrator for creating new folders.",
                            type="negative",
                        )
                        return
                    await db.execute(
                        "INSERT INTO folders(name, accessers, id) VALUES($1, $2, $3)",
                        f.value,
                        [roles[0].username],
                        str(uuid.uuid4()),
                    )
                    ui.notify("Refreshing in 2 seconds", type="ongoing")
                    await asyncio.sleep(2)
                    ui.open("/")

                ui.button("Submit", on_click=create_new_folder)
            return dialog.open
        buttons = []
        role = await db.fetch(
                        "SELECT roles FROM users WHERE session = $1",
                        str(app.storage.user.get("authenticator")),
                        record_class=UserRecord,
                    )
        if role[0].roles in ["admin", "uploaders"]:
            buttons = [
                CustomButtonBuilder(popup_thigmajig()).props(
                    "flat color=white icon=create_new_folder"
                )
            ]
        await show_header(
            db,
            "Listing",
            buttons
        )
        await say_hi(db)
        # ui.separator()
        with ui.row(wrap=True).classes("items-start justify-center gap-10 m-4"):
            async with db.acquire() as d:
                x: list[UserRecord] = await db.fetch(
                    "SELECT roles FROM users WHERE session = $1",
                    str(app.storage.user.get("authenticator")),
                    record_class=UserRecord,
                )
                if x:
                    if x[0].roles == "admin":
                        a = await d.fetch(
                            "SELECT * FROM folders", record_class=FolderRecord
                        )
                    else:
                        a = await d.fetch(
                            "SELECT * FROM folders WHERE (SELECT username FROM users WHERE session = $1) = ANY(accessers);",
                            str(app.storage.user.get("authenticator")),
                            record_class=FolderRecord,
                        )
               else:
                    raise Exception("???")
                for f in a:
                    # print(f)
                    with ui.column().classes("w-auto h-auto"):
                        j = f.id
                        # print(j)

                        def v(
                            j=j,
                        ):
                            # print(j)
                            ui.open(f"/folder/{j}")

                        with ui.button(on_click=v).classes(
                            "flex flex-col items-center justify-center"
                        ):
                            ui.icon("folder", size="md", color="darkorange")
                            ui.label(f"{f.name} (ID: {f.id})")
