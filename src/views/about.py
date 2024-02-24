import os
from pathlib import Path

import asyncpg
import fastapi
import humanize
from nicegui import app, ui

from ..models import FileRecord, FolderRecord, UserRecord
from .utils import show_header


def install(fapp: fastapi.FastAPI, db: asyncpg.Pool):
    @ui.page("/about")
    async def about(folder_id: str, file_id: str):
        await show_header(db, "About")
        await ui.label("About").style("justify-content: center")