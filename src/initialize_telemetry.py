import logfire.integrations
import opentelemetry.instrumentation.asyncio
import opentelemetry.instrumentation.asyncpg
import opentelemetry.instrumentation.fastapi
import logfire

import fastapi

def initialize_telemetry(app: fastapi.FastAPI):
    opentelemetry.instrumentation.asyncio.AsyncioInstrumentor().instrument()
    opentelemetry.instrumentation.asyncpg.AsyncPGInstrumentor(False).instrument()
    opentelemetry.instrumentation.fastapi.FastAPIInstrumentor().instrument_app(app)
    logfire.instrument_asyncpg()
    logfire.instrument_fastapi(app)