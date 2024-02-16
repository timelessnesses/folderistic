import asyncpg
from dotenv import load_dotenv

load_dotenv()
import os

import bcrypt


async def add():
    db = await asyncpg.create_pool(host=os.getenv("FOLDERISTIC_HOST"), user=os.getenv("FOLDERISTIC_USER"), password=os.getenv("FOLDERISTIC_PASS"), database=os.getenv("FOLDERISTIC_DB"))  # type: ignore
    assert db != None, "Pool returns None?"
    print("Connected to database")
    user = input("Username: ")
    await db.execute("""
    DELETE FROM authenticated WHERE username = $1
                     """, user)
    print("Done!")


import asyncio

asyncio.run(add())
