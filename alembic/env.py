import asyncio
from logging.config import fileConfig
from sqlalchemy import create_engine, pool
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from src.infrastructure.database.connection import Base
from src.infrastructure.models.user import UserModel
from src.infrastructure.models.otp import OTPModel
from src.infrastructure.models.forgetToken import ForgotPasswordToken
from alembic import context

# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
config.set_main_option('sqlalchemy.url', 'postgresql+asyncpg://postgres:postgres@localhost:5433/auth_database')

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata  # Assuming Base is where all models are defined

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5433/auth_database",
        echo=True,
        poolclass=pool.NullPool,
    )

    # Create the async session for transaction management
    async with connectable.connect() as connection:
        async with connection.begin():
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
            )
            await context.run_migrations()


def run_migrations() -> None:
    """Main function to handle migration execution."""
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        asyncio.run(run_migrations_online())  # Ensure async is run properly


if __name__ == "__main__":
    run_migrations()
