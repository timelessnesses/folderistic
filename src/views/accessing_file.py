import os
from pathlib import Path

import asyncpg
import fastapi
import humanize
from nicegui import app, ui, Client

from ..models import FileRecord, FolderRecord, UserRecord
from .utils import show_header


def install(fapp: fastapi.FastAPI, db: asyncpg.Pool):
    @ui.page("/folder/{folder_id}/{file_id}")
    async def accessing_file(folder_id: str, file_id: str, client: Client):
        async with db.acquire() as d:

            async def get_file_id(file_id: str):
                file_path = (
                    await d.fetch(
                        "SELECT path FROM files WHERE id = $1",
                        file_id,
                        record_class=FileRecord,
                    )
                )[0]
                return humanize.naturalsize(Path(file_path.path).stat().st_size)

            if (
                len(
                    x := await d.fetch(
                        "SELECT * FROM files WHERE folder = $1 AND id = $2",
                        folder_id,
                        file_id,
                        record_class=FileRecord,
                    )
                )
                == 0
            ):
                await show_header(None, "Listing - Folder - Unknown File", client)
                with ui.card().classes("absolute-center"):
                    ui.label("File not found!")
                ui.notify(
                    "File not found! Redirect back to folder in 3 seconds",
                    type="negative",
                )
                ui.timer(3, lambda: ui.open(f"/folder/{folder_id}"))
                return
            file = x[0]
            folder = (
                await d.fetch(
                    "SELECT * FROM folders WHERE id = $1",
                    folder_id,
                    record_class=FolderRecord,
                )
            )[0]
            await show_header(db, f"Folder {folder.name} - {file.name}", client)
            with ui.column().classes("w-auto h-auto"):
                with ui.row().classes("items-center justify-center"):
                    ui.label(f"Folder: {folder.name} ({file.folder})")
                    ui.label(f"File: {file.name} ({file.id})")
                    ui.label(
                        f"When uploaded: {str(file.last_updated).replace('-', '/').split('.')[0]}"
                    )
                    ui.label(f"Who uploaded this file: {file.who}")
            ui.separator()
            with ui.column().classes("w-auto h-auto"):
                with ui.row().classes("items-center justify-center"):

                    async def download():
                        ui.download(
                            f"/folder/{folder_id}/{file_id}/download", file.name
                        )

                    ui.button(
                        f"Download ({await get_file_id(file.id)})", on_click=download
                    )
                    user = (
                        await d.fetch(
                            "SELECT * from users WHERE session = $1",
                            str(app.storage.user.get("authenticator")),
                            record_class=UserRecord,
                        )
                    )[0]

                    async def delete_file(id: str):
                        os.remove(file.path)
                        await d.execute("DELETE FROM files WHERE id = $1", id)

                    if user.roles == "admin":
                        ui.button(
                            f"Delete", on_click=lambda: delete_file(file.id)
                        ).props("color=red")

    @fapp.get("/folder/{folder_id}/{file_id}/download")
    async def download_thing(
        folder_id: str, file_id: str
    ) -> fastapi.responses.FileResponse:
        async with db.acquire() as d:
            file = (
                await d.fetch(
                    "SELECT * FROM files WHERE id = $1 AND folder = $2",
                    file_id,
                    folder_id,
                    record_class=FileRecord,
                )
            )[0]
            return fastapi.responses.FileResponse(file.path, filename=file.name)
