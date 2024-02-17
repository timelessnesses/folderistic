import uuid

import asyncpg
import asyncio
import bcrypt
from nicegui import app, ui

from .utils import show_menu, show_header
from ..models import FileRecord, FolderRecord

def install(db: asyncpg.Pool):
    @ui.page("/{folder_id}")
    async def get_contents(folder_id: str):
        async def a():
            ui.notify("Redirecting back in 3 seconds",type="ongoing")
            await asyncio.sleep(3)
            ui.open("/")
        async with db.acquire() as d:
            folder = await d.fetch("SELECT * FROM folders WHERE id = $1", folder_id, record_class=FolderRecord)
            if len(folder) == 0:
                await show_header(db, f"Unknown Folder")
                with ui.card().classes("absolute-center"):
                    ui.label("Folder is NOT recorded!")# .classes("flex flex-col items-center justify-center")
                    ui.button("Go Back", on_click=a).classes("justify-center")# .classes("flex flex-col items-center justify-center")
                return
            files = await d.fetch("SELECT * FROM files WHERE folder = $1", folder_id, record_class=FileRecord)
            await show_header(db, f"Listing - Folder {folder[0].name} (ID: {folder[0].id})")
            