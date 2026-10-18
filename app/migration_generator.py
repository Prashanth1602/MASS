
from pathlib import Path


class MigrationGenerator:
    """Generate Alembic migration infrastructure for an application."""

    def generate(self, output_directory: Path) -> list[str]:
        alembic_directory = output_directory / "alembic"
        versions_directory = alembic_directory / "versions"

        versions_directory.mkdir(parents=True, exist_ok=True)

        env_file = alembic_directory / "env.py"
        env_file.write_text(
            '''import os

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.database import Base

try:
    from app.authentication import models as authentication_models
except ImportError:
    authentication_models = None

config = context.config
target_metadata = Base.metadata


def get_database_url():
    return os.environ["DATABASE_URL"]


def run_migrations_offline():
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    configuration = config.get_section(
        config.config_ini_section
    )
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
''',
            encoding="utf-8",
        )

        ini_file = output_directory / "alembic.ini"
        ini_file.write_text(
            """[alembic]
script_location = alembic
prepend_sys_path = .
"""
        , encoding="utf-8")

        template_file = alembic_directory / "script.py.mako"
        template_file.write_text(
            '''"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
''',
            encoding="utf-8",
        )

        return [str(env_file), str(ini_file)]
