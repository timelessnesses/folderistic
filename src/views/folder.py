import asyncio
import datetime
import os
import uuid

import asyncpg
import bcrypt
from nicegui import app, ui
from nicegui.events import UploadEventArguments

from ..models import FileRecord, FolderRecord, UserRecord
from .utils import CustomButtonBuilder, show_header, show_menu


def install(db: asyncpg.Pool):
    @ui.page("/folder/{folder_id}")
    async def get_contents(folder_id: str):
        async def a():
            ui.notify("Redirecting back in 3 seconds", type="ongoing")
            await asyncio.sleep(3)
            ui.open("/")

        async def create_folders(folders: str):
            try:
                os.mkdir("files")
            except FileExistsError:
                pass
            try:
                os.mkdir(folders)
            except FileExistsError:
                pass

        async def upload_event(u: UploadEventArguments):
            file = u.content
            file_id = uuid.uuid4()
            try:
                ui.notify("Saving file to disk", type="ongoing")
                with open(f"files/{folder_id}/{str(file_id)}", "wb") as fp:
                    fp.write(file.read())
            except Exception:
                ui.notify(
                    "Exception: Failed to write file. Creating new folder.",
                    type="ongoing",
                )
                await create_folders(f"files/{folder_id}")
                ui.notify("Created folder. Processing file again.", type="ongoing")
                return await upload_event(u)
            async with db.acquire() as d:
                ui.notify("Recording file to the database", type="ongoing")
                user = (await d.fetch("SELECT * FROM users WHERE session = $1", str(app.storage.user.get("authenticator")), record_class=UserRecord))[0]
                await d.execute(
                    "INSERT INTO files(folder, id, last_updated, path, name, who) VALUES ($1, $2, $3, $4, $5, $6)",
                    folder_id,
                    str(file_id),
                    datetime.datetime.now(),
                    f"files/{folder_id}/{file_id}",
                    u.name,
                    user.username
                )
                ui.notify(
                    f"Successfully uploaded your file! ({u.name}) Refreshing in 3 seconds",
                    type="positive",
                )
                ui.timer(3, lambda: ui.open(f"/folder/{folder_id}"))

        async def file_upload_popup():
            print("i got clicked")
            with ui.dialog(value=True):
                with ui.card().classes("fixed-center absolute-center"):
                    ui.label(
                        "Please drag your files to the box under this text or just click on plus sign."
                    )
                    ui.upload(
                        multiple=True,
                        label="Drag your files here or click me!",
                        on_upload=upload_event,
                    )

        async with db.acquire() as d:
            folder = await d.fetch(
                "SELECT * FROM folders WHERE id = $1",
                folder_id,
                record_class=FolderRecord,
            )
            if len(folder) == 0:
                await show_header(None, f"Unknown Folder")
                with ui.card().classes("absolute-center"):
                    ui.label(
                        "Folder is not exists!"
                    )  # .classes("flex flex-col items-center justify-center")
                    ui.button("Go Back", on_click=a).classes(
                        "justify-center"
                    )  # .classes("flex flex-col items-center justify-center")
                    ui.notify(
                        "Folder is not exists! Redirecting you in 3 seconds.",
                        type="negative",
                    )
                    ui.timer(5, callback=lambda: ui.open("/"))
                return
            files = await d.fetch(
                "SELECT * FROM files WHERE folder = $1",
                folder_id,
                record_class=FileRecord,
            )
            role = await d.fetch(
                "SELECT roles FROM users WHERE session = $1",
                str(app.storage.user.get("authenticator")),
                record_class=UserRecord,
            )
            if role[0].roles in ["admin", "uploaders"]:
                buttons = [
                    CustomButtonBuilder(on_click=file_upload_popup).props(
                        "flat color=white icon=file_upload"
                    )
                ]
            else:
                buttons = None
            await show_header(
                db, f"Listing - Folder {folder[0].name} (ID: {folder[0].id})", buttons
            )
            with ui.row(wrap=True).classes("items-start justify-center gap-10 m-4"):
                for f in files:
                    print(f)
                    with ui.column().classes("w-auto h-auto"):
                        j = f.id
                        print(j)

                        # Define the on_click function with a default argument to capture the current value of `j`
                        def v(
                            j=j,
                        ):  # This captures the current value of `j` for each iteration
                            print(j)
                            ui.open(f"/folder/{folder_id}/{j}")

                        with ui.button(on_click=v).classes(
                            "flex flex-col items-center justify-center"
                        ):
                            ui.icon("description", size="md", color="darkorange")
                            ui.label(f"{f.name} (ID: {f.id})")
