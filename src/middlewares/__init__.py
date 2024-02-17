import asyncpg
import fastapi

from . import auth

# import typing

# APP = typing.TypeVar("APP", bound=fastapi.FastAPI)


def install_middlewares(app: fastapi.FastAPI):
    app.add_middleware(auth.AuthMiddleWare)
