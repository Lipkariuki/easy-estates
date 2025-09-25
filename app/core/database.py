from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

engine = create_engine(settings.database_url, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

from contextlib import contextmanager
@contextmanager
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
