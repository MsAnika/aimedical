from __future__ import with_statement
import os

from alembic import context
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from dotenv import load_dotenv

# Load .env file in the project root (two levels up from this file)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# looking for DATABASE_URL env var
database_url = os.getenv("DATABASE_URL")

if database_url:
    # override the sqlalchemy.url from ini if present
    os.environ["SQLALCHEMY_URL"] = database_url

target_metadata = None

def run_migrations_offline():
    url = context.get_x_argument().get("dburl")
    if not url:
        url = os.getenv("SQLALCHEMY_URL") or "sqlite:///./meddiag.db"
    context.configure(url=url, target_metadata=target_metadata,
                    literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        {"sqlalchemy.url": os.getenv("SQLALCHEMY_URL", "sqlite:///./meddiag.db")},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()