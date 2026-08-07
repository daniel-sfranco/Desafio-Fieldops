from os import getenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = getenv(
    "DATABASE_URL",
    f"postgresql://{getenv('POSTGRES_USER', 'postgres')}:{getenv('POSTGRES_PASSWORD', 'postgres')}@{getenv('POSTGRES_HOST', 'localhost')}:{getenv('POSTGRES_PORT', '5432')}/{getenv('POSTGRES_DB', 'fieldops')}"
)

engine = create_engine(DATABASE_URL)
sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
base = declarative_base()

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()
