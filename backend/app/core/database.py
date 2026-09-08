from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

import os

# ------------------------------------------------------------------
# 1️⃣  SQLite → PostgreSQL (Alembic‑enabled)
# ------------------------------------------------------------------
# Read DATABASE_URL from the environment; if it is not set we fall back
# to the original SQLite file so the demo still works out‑of‑the‑box.
_database_url = os.getenv(
    "DATABASE_URL",
    "sqlite:///./meddiag.db",
)

engine = create_engine(
    _database_url,
    connect_args={"check_same_thread": False}
    if _database_url.startswith("sqlite")
    else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()