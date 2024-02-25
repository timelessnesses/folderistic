import asyncpg
from nicegui import ui, Client

from .utils import show_header

# from ..models import UserRecord, FolderRecord


def install(_: asyncpg.Pool):
    @ui.page("/failed_auth")
    async def failed_auth(client: Client):
        await show_header(None, "Unauthorized", client)
        with ui.card().classes("absolute-center"):
            ui.label(
                "You are NOT authorized! Please login. We will redirect you in 3 seconds"
            )
            ui.notify(
                "You are NOT authorized! Please login. We will redirect you in 3 seconds",
                type="negative",
            )
            ui.timer(3, lambda: ui.open("/login"), once=True)
