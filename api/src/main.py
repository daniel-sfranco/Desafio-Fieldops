from contextlib import asynccontextmanager
from fastapi import FastAPI

from routes import auth
from utils.database import engine, base
from utils.exceptions import register_exception_handlers
import models


@asynccontextmanager
async def lifespan(app: FastAPI):
    base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="FieldOps Lite API",
    version="2026.2",
    lifespan=lifespan
)

app.include_router(auth.router)

register_exception_handlers(app)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "apiRevision": "2026.2",
        "service": "fieldops-lite"
    }
