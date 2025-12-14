import asyncio
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.config import Config
from uvicorn.server import Server

from api.router import router
from config.logger import configure_logger
from domain.util import stop_event
from infrastructure.db.db import sessionmanager


configure_logger()


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup events

    yield

    # shutdown events
    stop_event.set()
    await sessionmanager.close()


app = FastAPI(
    lifespan=lifespan,
    root_path="/api",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешенные источники
    allow_credentials=True,
    allow_methods=["*"],  # Разрешите все методы или укажите конкретные
    allow_headers=["*"],  # Разрешите все заголовки или укажите конкретные
)


@app.middleware("http")
async def log_request_response(request: Request, call_next):
    response = await call_next(request)
    if response.status_code not in [200]:
        logger.info(f"Request: {request.method} {request.url} - Response: {response.status_code}")
    return response


app.include_router(router)


async def run_fastapi():
    config = Config(app=app, host="0.0.0.0", port=9000, lifespan="on", log_level="warning")
    server = Server(config)
    await server.serve()


async def main() -> None:
    await asyncio.gather(
        run_fastapi(),
    )


if __name__ == "__main__":
    asyncio.run(main())
