from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from src.app.core.config import settings

# For SQLite, we need to allow multi-threaded access for FastAPI
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autoflush=False, bind=engine)

Base = declarative_base()
