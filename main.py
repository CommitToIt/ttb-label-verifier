from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.logging_config import configure_logging
from app.routes import router

BASE_DIR = Path(__file__).parent


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    yield


app = FastAPI(title="TTB Label Verifier", lifespan=lifespan)
app.include_router(router, prefix="/api")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.mount("/", StaticFiles(directory=BASE_DIR / "static", html=True), name="static")
