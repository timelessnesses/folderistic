import asyncpg
from nicegui import ui

from .utils import show_header

# from ..models import UserRecord, FolderRecord


def install(_: asyncpg.Pool):
    @ui.page("/failed_auth")
    async def failed_auth():
        await show_header(None, "Unauthorized")
        with ui.card().classes("absolute-center"):
            ui.label(
                "You are NOT authorized! Please login. We will redirect you in 3 seconds"
            )
            ui.notify(
                "You are NOT authorized! Please login. We will redirect you in 3 seconds",
                type="negative",
            )
            ui.timer(3, lambda: ui.navigate.to("/login"), once=True)
