import asyncio
import datetime
import io
import os
import uuid
import zipfile
import copy

import asyncpg
from nicegui import app, ui
from nicegui.events import UploadEventArguments

from ..models import FileRecord, FolderRecord, UserRecord
from .utils import CustomButtonBuilder, show_header


def install(db: asyncpg.Pool):
    @ui.page("/folder/{folder_id}")
    async def get_contents(folder_id: str):
        async def a():
            ui.notify("Redirecting back in 5 seconds", type="ongoing")
            await asyncio.sleep(5)
            ui.open("/")
        async with db.acquire() as d:
            role = await d.fetch("SELECT username, roles FROM users WHERE session = $1", str(app.storage.user["authenticator"]), record_class=UserRecord)
            accessers = await d.fetch("SELECT accessers FROM folders WHERE id = $1", folder_id, record_class=FolderRecord)
            print(role, accessers)
            if role[0].username not in accessers or role[0].roles != "admin":
                await show_header(db, f"Inaccessible Folder")
                with ui.card().classes("absolute-center"):
                    ui.label(
                        "Folder is not accessible!"
                    )  # .classes("flex flex-col items-center justify-center")
                    ui.button("Go Back", on_click=a).classes(
                        "justify-center"
                    )  # .classes("flex flex-col items-center justify-center")
                    ui.notify(
                        "Folder is not accessible! Redirecting you in 5 seconds.",
                        type="negative",
                    )
                    ui.timer(5, callback=lambda: ui.open("/"))
                return

        async def create_folders(folders: str):
            try:
                os.mkdir("files")
            except FileExistsError:
                pass
            try:
                os.mkdir(folders)
            except FileExistsError:
                pass

        async def upload_event(u: UploadEventArguments, n: ui.notification | None = None):
            if not n:
                n = ui.notification(timeout=None, type="positive")
            file = u.content
            file_id = uuid.uuid4()
            n.spinner = True
            n.message = "Processing"
            try:
                with open(f"files/{folder_id}/{str(file_id)}", "wb") as fp:
                    fp.write(file.read())
            except Exception:
                await create_folders(f"files/{folder_id}")
                return await upload_event(u, n)
            async with db.acquire() as d:
                user = (
                    await d.fetch(
                        "SELECT * FROM users WHERE session = $1",
                        str(app.storage.user.get("authenticator")),
                        record_class=UserRecord,
                    )
                )[0]
                await d.execute(
                    "INSERT INTO files(folder, id, last_updated, path, name, who) VALUES ($1, $2, $3, $4, $5, $6)",
                    folder_id,
                    str(file_id),
                    datetime.datetime.now(),
                    f"files/{folder_id}/{file_id}",
                    u.name,
                    user.username,
                )
                n.message = f"Successfully uploaded your file! ({u.name}) Please refresh manually"
                ui.timer(5, n.dismiss, once=True)
                ui.timer(5, lambda: ui.open(f"/folder/{folder_id}"))

        async def file_upload_popup():
            with ui.dialog(value=True):
                with ui.card().classes("fixed-center absolute-center"):
                    ui.label(
                        "Please drag your files to the box under this text or just click on plus sign."
                    )
                    ui.upload(
                        multiple=True,
                        label="Drag your files here or click me!",
                        on_upload=lambda u: upload_event(u),
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
                        "Folder is not exists! Redirecting you in 5 seconds.",
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
            buttons: list[CustomButtonBuilder] = []
            if role[0].roles in ["admin", "uploaders"]:
                buttons.append(
                    CustomButtonBuilder(on_click=file_upload_popup).props(
                        "flat color=white icon=file_upload"
                    )
                )

            async def add_people():
                with ui.dialog(value=True), ui.card():
                    ui.label(
                        "Users that have access to this folder (All administrators will have a access to every folder but they may not show up here.) (Submitting same name that is in accessible users will remove them)"
                    )
                    with ui.element("q-list").props("bordered separator"):
                        async with db.acquire() as d:
                            users = (
                                await d.fetch(
                                    "SELECT accessers FROM folders WHERE id = $1",
                                    folder_id,
                                    record_class=FolderRecord,
                                )
                            )[0]
                            for user in users.accessers:
                                with ui.element("q-item"):
                                    with ui.element("q-item-section"):
                                        ui.label(user)

                    async def add_user():
                        usernames: list[str] = username.value.strip().split(",")
                        remove = []
                        for u in copy.copy(usernames):
                            if u in users.accessers:
                                usernames.remove(u)
                                remove.append(u)
                            if not username:
                                usernames.remove(u)
                                remove.append(u)
                        async with db.acquire() as d:
                            await d.execute(
                                """
                                UPDATE folders
                                SET accessers = ARRAY(
                                    SELECT DISTINCT unnest
                                    FROM (
                                        SELECT unnest(accessers) 
                                        UNION 
                                        SELECT unnest($2::text[])
                                    ) s
                                )
                                WHERE id = $1
                                            """,
                                folder_id,
                                usernames,
                            )
                            await d.execute(
                                """
                                UPDATE folders
                                SET accessers = (
                                    SELECT array_agg(a)
                                    FROM (
                                        SELECT unnest(accessers) AS a
                                        FROM folders
                                        WHERE id = $1
                                    ) AS unnested
                                    WHERE a <> ALL($2)
                                )
                                WHERE id = $1;
                                """, folder_id, remove
                            )
                            ui.notify(
                                "Successfully added new users to be able to access this folder!",
                                type="positive",
                            )
                            ui.timer(3, lambda: ui.open(f"/folder/{folder_id}"))
                    async with db.acquire() as d:
                        usernames = await d.fetch("SELECT username FROM users", record_class=UserRecord)
                    username = ui.input(
                        "Input your username here splitting by commas",
                        autocomplete=[x.username for x in usernames],
                    )
                    ui.button("Submit", on_click=add_user)

            if role[0].roles == "admin":
                buttons.append(
                    CustomButtonBuilder(on_click=add_people).props(
                        "flat color=white icon=person_add"
                    )
                )

            async def zip_files_then_download():
                notification = ui.notification(timeout=None)
                notification.spinner = True
                notification.message = "Processing"
                zipped = io.BytesIO()
                # notification.message = "Initializing ZipFile In Memory"
                with zipfile.ZipFile(
                    zipped, "a", zipfile.ZIP_DEFLATED, False
                ) as zipper:
                    # notification.message = "Getting all files in the folder"
                    async with db.acquire() as d:
                        files = await d.fetch(
                            "SELECT * from files WHERE folder = $1",
                            folder_id,
                            record_class=FileRecord,
                        )
                    # notification.message = "Successfully got all files"
                    file_names = []
                    for file in files:
                        if file.name in file_names:
                            name, ext = os.path.splitext(file.name)
                            file_name = name + str(uuid.uuid4()) + ext
                        else:
                            file_name = file.name
                        zipper.write(file.path, file_name)
                zipped.seek(0)
                ui.download(zipped.read(), f"{folder[0].name} ({folder[0].id}).zip")
                notification.message = "Sending download request"
                notification.spinner = True
                notification.message = "Enjoy your download!"
                notification.spinner = False
                notification.type = "positive"
                ui.timer(3, notification.dismiss, once=True)

            buttons.append(
                CustomButtonBuilder(on_click=zip_files_then_download).props(
                    "flat color=white icon=folder_zip"
                )
            )
            await show_header(
                db, f"Listing - Folder {folder[0].name} (ID: {folder[0].id})", buttons
            )
            with ui.row(wrap=True).classes("items-start justify-center gap-10 m-4"):
                for f in files:
                    with ui.column().classes("w-auto h-auto"):
                        j = f.id

                        def v(
                            j=j,
                        ):  # This captures the current value of `j` for each iteration
                            ui.open(f"/folder/{folder_id}/{j}")

                        with ui.button(on_click=v).classes(
                            "flex flex-col items-center justify-center"
                        ):
                            ui.icon("description", size="md", color="darkorange")
                            ui.label(f"{f.name} (ID: {f.id})")
