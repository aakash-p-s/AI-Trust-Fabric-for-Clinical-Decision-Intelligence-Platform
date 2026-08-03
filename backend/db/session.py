"""
backend/db/session.py
Engine + session factory. Reads DATABASE_URL from the environment.
Works against PostgreSQL (default, via docker-compose.yml) or SQLite
(fallback -- see .env.example).
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://trust_fabric:trust_fabric_dev_password@localhost:5432/trust_fabric",
)

engine_kwargs: dict = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    engine_kwargs["poolclass"] = StaticPool

engine = create_engine(DATABASE_URL, **engine_kwargs, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db():
    """FastAPI dependency: yields a SQLAlchemy session, always closed after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_engine():
    """Called once on FastAPI startup to verify the DB connection is reachable."""
    with engine.connect():
        pass
