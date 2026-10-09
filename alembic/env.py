from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Our single source of configuration (reads .env).
from app.config import settings

# Base.metadata holds the description of every table that inherits from Base.
from app.database.base import Base

# Importing app.models registers User and Task on Base.metadata.
# Without this line, autogenerate would think there are no tables.
import app.models  # noqa: F401

# Alembic's config object (gives access to alembic.ini values).
config = context.config

# Set up Python logging as configured in alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Inject the real database URL from .env at runtime.
# "%" is special in .ini-style config, so we escape it (matters if a password contains %).
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("%", "%%"))

# What Alembic compares the real database against.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Offline mode: generate SQL text without connecting to the database."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Online mode (normal): connect to the database and apply migrations."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # no connection pooling needed for a one-off command
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()