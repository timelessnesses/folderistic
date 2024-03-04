from nicegui import app, Client
import asyncpg
import datetime
def install(db: asyncpg.Pool):
    async def on_connect(client: Client):
        await db.execute("UPDATE users SET first_connected = $2 WHERE session = $1", str(app.storage.user["authenticator"]), datetime.datetime.now())
        
    async def on_disconnect(client: Client):
        await db.execute("UPDATE users SET last_connected = $2 WHERE session = $1", str(app.storage.user["authenticator"]), datetime.datetime.now())
    
    app.on_connect(on_connect)
    app.on_disconnect(on_disconnect)
    
    