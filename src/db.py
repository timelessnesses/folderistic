import sqlalchemy
from dotenv import load_dotenv
load_dotenv()
import os
import typing
import sqlalchemy.ext.asyncio
import sqlalchemy.orm
import sqlalchemy.ext.declarative

DB_TYPE: typing.Literal["postgresql", "mysql", "sqlite", "oracle", "mssql"] = os.getenv("FOLDERISTIC_DB_TYPE", "sqlite") # type: ignore
DB_ENGINE = os.getenv("FOLDERISTIC_DB_ENGINE", "")

DB_USER = os.getenv("FOLDERISTIC_DB_USER")
DB_PASSWORD = os.getenv("FOLDERISTIC_DB_PASSWORD")
DB_HOST = os.getenv("FOLDERISTIC_DB_HOST")
DB_PORT = int(os.getenv("FOLDERISTIC_DB_PORT", ""))
DB_NAME = os.getenv("FOLDERISTIC_DB_NAME")

VALID_DATABASES = [
    "postgresql",
    "mysql",
    "sqlite",
    "oracle",
    "mssql"
]

VALID_POSTGRES_ENGINES = [
    "asyncpg",
    "psycopg",
    "psycopg_async"
]

VALID_MYSQL_ENGINES = [
    "asyncmy",
    "aiomysql",
]

VALID_SQLITE_ENGINES = [
    "aiosqlite",
]

VALID_ORACLE_ENGINES = [
    "oracledb",
    "oracledb_async"
]

VALID_MSSQL_ENGINES = [
    "aioodbc",
]

checks = {
    "postgresql": VALID_POSTGRES_ENGINES,
    "mysql": VALID_MYSQL_ENGINES,
    "sqlite": VALID_SQLITE_ENGINES,
    "oracle": VALID_ORACLE_ENGINES,
    "mssql": VALID_MSSQL_ENGINES
}

assert DB_ENGINE in checks[DB_TYPE] or DB_ENGINE == "", "Database engine is not in supported engines."
if DB_ENGINE == "":
    if DB_TYPE == "mssql":
        DB_ENGINE = "aioodbc"
    elif DB_TYPE == "mysql":
        DB_ENGINE = "aiomysql"
    elif DB_TYPE == "oracle":
        DB_ENGINE = "oracledb_async"
    elif DB_TYPE == "postgresql":
        DB_ENGINE = "asyncpg"
    elif DB_TYPE == "sqlite":
        DB_ENGINE = "aiosqlite"

url = sqlalchemy.URL.create(
    f"{DB_TYPE}+{DB_ENGINE}",
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT,
    DB_NAME
)

engine = sqlalchemy.ext.asyncio.create_async_engine(url, connect_args={
    "check_same_thread": False,
    "jit": False
})

session = sqlalchemy.ext.asyncio.async_sessionmaker(engine)
Base = sqlalchemy.ext.declarative.declarative_base()