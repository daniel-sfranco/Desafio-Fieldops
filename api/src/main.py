import sys
from pathlib import Path

# Garante que o diretório 'src' esteja no PYTHONPATH para resolver as importações
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from contextlib import asynccontextmanager
from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from routes import auth, work_order
from utils.database import engine, base
from utils.exceptions import register_exception_handlers
import models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="FieldOps Lite API",
    version="2026.2",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(work_order.router)

register_exception_handlers(app)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "apiRevision": "2026.2",
        "service": "fieldops-lite"
    }
