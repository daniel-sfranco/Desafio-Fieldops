from contextlib import asynccontextmanager
from fastapi import FastAPI

from database import engine, base
import models  # garante o registro de todos os modelos no metadata do SQLAlchemy


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria todas as tabelas no banco se elas ainda não existirem na inicialização da API
    base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="FieldOps Lite API",
    version="2026.2",
    lifespan=lifespan
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "apiRevision": "2026.2",
        "service": "fieldops-lite"
    }
