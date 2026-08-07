from os import getenv
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Carrega as variáveis do arquivo .env localizado na raiz do projeto
load_dotenv(find_dotenv(usecwd=True))

DATABASE_URL = getenv("DATABASE_URL")

if not DATABASE_URL:
    user = getenv("POSTGRES_USER", "flx")
    password = getenv("POSTGRES_PASSWORD", "password123")
    host = getenv("POSTGRES_HOST", "localhost")
    port = getenv("POSTGRES_PORT", "5433")
    db_name = getenv("POSTGRES_DB", "flx_db")
    DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"

engine = create_engine(DATABASE_URL)
sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
base = declarative_base()

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()
