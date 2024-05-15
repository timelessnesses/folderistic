import os
import shutil
import threading
import uuid

import asyncpg
import fastapi
import prometheus_client
import psutil
import starlette_exporter
from dotenv import load_dotenv
from nicegui import Client, app, ui
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from prometheus_fastapi_instrumentator.metrics import Info
import logfire

load_dotenv()
import os

from . import middlewares
from .initialize_telemetry import initialize_telemetry
from .views import install
from .views.utils import db_ping

db = asyncpg.create_pool(host=os.getenv("FOLDERISTIC_HOST"), user=os.getenv("FOLDERISTIC_USER"), password=os.getenv("FOLDERISTIC_PASS"), database=os.getenv("FOLDERISTIC_DB"))  # type: ignore
initialized_db = False

@app.on_startup
async def ls():
    global db, initialized_db
    with logfire.span("Connecting to database"):
        if not initialized_db:
            try:
                a = await db
                assert a is not None
                db = a
            except:
                pass
            finally:
                initialized_db = True
        install(app, db)
    logfire.info("Connected to database successfully")
    with open("./src/types.sql") as s:
        try:
            await db.execute(s.read())  # type: ignore
        except:
            pass
        finally:
            logfire.info("Executed types statements")
    with open("./src/start.sql") as s:
        await db.execute(s.read())  # type: ignore
        logfire.info("Executed starter statements")


@app.on_shutdown
async def die():
    if not initialized_db:
        logfire.info("Closing database")
        await db.close()


try:
    with open("./SECRET.uuid4") as fp:
        secret = fp.read()
except FileNotFoundError:
    secret = str(uuid.uuid4())
    with open("./SECRET.uuid4", "w") as fp:
        fp.write(secret)
app.add_middleware(middlewares.auth.AuthMiddleWare, database=db)
logfire.info("Added authentication middleware")
app.add_middleware(starlette_exporter.middleware.PrometheusMiddleware)
logfire.info("Added prometheus middleware")


def db_latency():
    METRIC = prometheus_client.Gauge(
        "database_latency", "PostgreSQL Database Latency (Milliseconds)"
    )

    async def handle(_: Info):
        METRIC.set(await db_ping(db))

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
        for thread in threading.enumerate():
            if thread.is_alive():
                ALIVE.inc()
            if thread.daemon:
                DAEMON.inc()
            METRIC.inc()

    return handle


def users():
    ACTIVE = prometheus_client.Gauge(
        "active_users",
        "Amount of active users on Folderistic that is currently online and connected to server",
    )
    ALL = prometheus_client.Gauge("users", "Amount of users registered on the platform")

    async def handle(_: Info):
        ACTIVE.set_function(lambda: len(Client.instances.values()))
        async with db.acquire() as d:
            count = await d.fetch("SELECT COUNT(*) FROM users")
            ALL.set(count[0]["count"])

    return handle


def thingy(app: fastapi.FastAPI):
    prometheus = Instrumentator(should_instrument_requests_inprogress=True)
    prometheus.add(db_latency())
    prometheus.add(space_used())
    prometheus.add(ram_used())
    prometheus.add(cpu_usage())
    prometheus.add(threads())
    prometheus.add(users())
    prometheus.add(metrics.latency())
    prometheus.add(metrics.requests())

    prometheus.instrument(app)
    prometheus.expose(app)
    
    app.add_route("/metrics-starlette", starlette_exporter.handle_metrics)
    initialize_telemetry(app)


thingy(app)
ui.run_with(
    app=fastapi.FastAPI(),
    title="Folderistic",
    dark=None,
    storage_secret=secret,
    favicon="./favicon.ico",
)
logfire.configure(console=False,send_to_logfire='if-token-present', collect_system_metrics=True, service_name="folderistic-main", project_name="folderistic", inspect_arguments=True, )