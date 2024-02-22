import asyncpg
from dotenv import load_dotenv

load_dotenv()
import getpass
import os
import random
import string
import typing
import bcrypt

def randomizer_pwd(length=20):
    return "".join([random.choice(string.ascii_letters + string.digits) for _ in range(length)])

async def add(pattern: str, accounts: int, default_role: typing.Literal["admin", "uploaders", "viewers"]):
    db = await asyncpg.create_pool(host=os.getenv("FOLDERISTIC_HOST"), user=os.getenv("FOLDERISTIC_USER"), password=os.getenv("FOLDERISTIC_PASS"), database=os.getenv("FOLDERISTIC_DB"))  # type: ignore
    assert db != None, "Pool returns None?"
    print("Connected to database")
    accounts_info: list[tuple[str, bytes, bytes, typing.Literal["admin", "uploaders", "viewers"]]] = []
    for x in range(accounts):
        user = pattern.format(x)
        password = randomizer_pwd()
        roles = default_role
        if roles.lower() not in ["admin", "uploaders", "viewers"]:
            assert False, "Role is not supported"
        salt = bcrypt.gensalt()
        salted_password = bcrypt.hashpw(password.encode(), salt)
        accounts_info.append((user, salted_password, salt, roles))
    async with db.acquire() as d:
        for user, salted_password, salt, roles in accounts_info:
            await d.execute(
                """
            INSERT INTO users(username, password, salt, roles) VALUES ($1, $2, $3, $4)
                            """,
                user,
                salted_password.hex(),
                salt.hex(),
                roles,
            )
    print("Done!")


import asyncio

asyncio.run(add(
    pattern=input("Input your username pattern (Support x variable): "),
    accounts=int(input("Amount of accounts you want to be generated: ")),
    default_role=input("Default roles for all of them: ") # type: ignore
))
