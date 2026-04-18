import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, owner, visitor, internal, bootstrap
from app.scheduler.worker import run_worker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(run_worker())
    yield
    task.cancel()


app = FastAPI(title="Agent Village", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(owner.router)
app.include_router(visitor.router)
app.include_router(internal.router)
app.include_router(bootstrap.router)
