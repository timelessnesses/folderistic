import asyncpg
from dotenv import load_dotenv

load_dotenv()
import os
import getpass

import bcrypt


async def add():
    db = await asyncpg.create_pool(host=os.getenv("FOLDERISTIC_HOST"), user=os.getenv("FOLDERISTIC_USER"), password=os.getenv("FOLDERISTIC_PASS"), database=os.getenv("FOLDERISTIC_DB"))  # type: ignore
    assert db != None, "Pool returns None?"
    print("Connected to database")
    user = input("Username: ")
    password = getpass.getpass("Password: ")
    salt = bcrypt.gensalt()
    salted_password = bcrypt.hashpw(password.encode(), salt)
    # d: asyncpg.Connection
    async with db.acquire() as d:
        await d.execute(
            """
        UPDATE users SET password = $2, salt = $3 WHERE user = $1
                        """,
            user,
            salted_password.hex(),
            salt.hex(),
        )
    print("Done!")


import asyncio

asyncio.run(add())
