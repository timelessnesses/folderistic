import asyncio
import os
import shutil
import threading
# import contextlib
# import typing
import uuid

import asyncpg
import fastapi
import prometheus_client
import psutil
import starlette_exporter
from dotenv import load_dotenv
from nicegui import app, ui
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from prometheus_fastapi_instrumentator.metrics import Info

load_dotenv()
import logging
import os

from . import middlewares
from .views import install
from .views.utils import db_ping

db = asyncpg.create_pool(host=os.getenv("FOLDERISTIC_HOST"), user=os.getenv("FOLDERISTIC_USER"), password=os.getenv("FOLDERISTIC_PASS"), database=os.getenv("FOLDERISTIC_DB"))  # type: ignore
initialized_db = False

@app.on_startup
async def ls():
    g = logging.getLogger("folderistic.startup")
    global db, initialized_db
    if not initialized_db:
        try:
            a = await db
            assert a is not None
            db = a
        except: pass
        finally:
            initialized_db = True
    install(app, db)
    if db is None:
        raise Exception("pool is none?")
    g.info("Connected to database")
    print("hi")
    with open("./src/start.sql") as s:
        await db.execute(s.read())  # type: ignore
        g.info("Executed starter statements")


@app.on_shutdown
async def die():
    if not initialized_db:
        await db.close()

try:
    with open("./SECRET.uuid4") as fp:
        secret = fp.read()
except FileNotFoundError:
    secret = str(uuid.uuid4())
    with open("./SECRET.uuid4", "w") as fp:
        fp.write(secret)
app.add_middleware(middlewares.auth.AuthMiddleWare, database=db)
app.add_middleware(starlette_exporter.middleware.PrometheusMiddleware)


def db_latency():
    METRIC = prometheus_client.Gauge(
        "database_latency", "PostgreSQL Database Latency (Milliseconds)"
    )

    async def handle(_: Info):
        global db, initialized_db
        if not initialized_db:
            try:
                a = await db
                assert a is not None
                db = a
            except: pass
            finally:
                initialized_db = True
        assert db is not None
        METRIC.set(await db_ping(db))
        await db.close()

    return handle


def space_used():
    USED = prometheus_client.Gauge("space_used", "Spaced used")
    LEFT = prometheus_client.Gauge("disk_space_left", "Total disk space left on root")

    def handle(_: Info):
        __, used, free = shutil.disk_usage("/")
        USED.set(used)
        LEFT.set(free)

    return handle


def ram_used():
    USED = prometheus_client.Gauge("ram_usage", "Amount of RAM being used")
    LEFT = prometheus_client.Gauge("ram_left", "Amount of RAM left that can be used")

    def handle(_: Info):
        x = psutil.virtual_memory()
        USED.set(x.used)
        LEFT.set(x.available)

    return handle


def cpu_usage():
    METRIC = prometheus_client.Gauge("cpu", "CPU Usage (Percent)")

    def handle(_: Info):
        METRIC.set(psutil.cpu_percent())

    return handle


def threads():
    METRIC = prometheus_client.Gauge("threads", "Amount of threads that is being used")
    DAEMON = prometheus_client.Gauge(
        "daemon_threads", "Threads that can let process exit safely"
    )
    ALIVE = prometheus_client.Gauge("alive_threads", "Threads that is actually alive")

    def handle(_: Info):
        j = 0
        for i, thread in enumerate(threading.enumerate(), start=1):
            j = i
            if thread.is_alive():
                ALIVE.inc()
            if thread.daemon:
                DAEMON.inc()

        METRIC.set(j)


def thingy(app: fastapi.FastAPI):
    prometheus = Instrumentator(should_instrument_requests_inprogress=True)
    prometheus.add(db_latency())
    prometheus.add(space_used())
    prometheus.add(ram_used())
    prometheus.add(cpu_usage())
    prometheus.add(threads())
    prometheus.add(metrics.latency())
    prometheus.add(metrics.requests())

    prometheus.instrument(app)
    prometheus.expose(app)

    app.add_route("/metrics-starlette", starlette_exporter.handle_metrics)


thingy(app)
ui.run_with(
    app=fastapi.FastAPI(),
    title="Folderistic",
    dark=None,
    storage_secret=secret,
    favicon="./favicon.ico",
)
