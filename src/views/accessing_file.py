import asyncpg
from nicegui import ui

from .utils import show_header

# from ..models import UserRecord, FolderRecord


def install(db: asyncpg.Pool):
    @ui.page("/folder/{folder_id}/{file_id}")
    async def accessing_file(folder_id: str, file_id: str):
        pass
