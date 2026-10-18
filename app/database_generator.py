
from pathlib import Path


class DatabaseGenerator:
    """Generate shared SQLAlchemy database infrastructure."""

    def generate(self, output_directory: Path) -> list[str]:
        core_directory = output_directory / "app" / "core"
        core_directory.mkdir(parents=True, exist_ok=True)

        init_file = core_directory / "__init__.py"
        init_file.touch(exist_ok=True)

        database_file = core_directory / "database.py"
        database_file.write_text(
'''import os

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker


database_url = URL.create(
    drivername="postgresql+psycopg",
    username=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    host=os.environ["POSTGRES_HOST"],
    port=int(os.environ.get("POSTGRES_PORT", "5432")),
    database=os.environ["POSTGRES_DB"],
)

engine = create_engine(database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''
,
            encoding="utf-8",
        )

        return [str(init_file), str(database_file)]