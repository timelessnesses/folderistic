import asyncio

import asyncpg
from nicegui import app, ui


async def show_menu(l: ui.drawer, db: asyncpg.Pool):
    async def logout():
        async with db.acquire() as d:
            name = await d.fetch(
                "SELECT username FROM users WHERE session = $1",
                str(app.storage.user.get("authenticator", "")),
            )
            if len(name) != 0:
                ui.notify(f"See you again! {name[0]['username']}")
                await asyncio.sleep(3)
        app.storage.user["authenticated"] = False
        app.storage.user["authenticator"] = None
        ui.open("/login")

    with l:
        ui.label("📂 Folderistic").style("font-size: 25px")
        if app.storage.user.get("authenticated", None):
            x = await db.fetch(
                "SELECT username, roles FROM users WHERE session = $1",
                str(app.storage.user.get("authenticator")),
            )
            username = x[0]["username"]
            role: str = x[0]["roles"]
            ui.label(f"User: {username} Role: {role.capitalize()}").style(
                "font-size: 15px"
            )
            ui.button("Logout", on_click=logout).classes("red")
        else:
            ui.button("Login", on_click=lambda: ui.open("/login"))

    def h():
        l.toggle()

    return h
