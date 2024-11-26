from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from src.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
engine = create_async_engine(settings.DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


logging.debug(f"Database URL: {engine.url}")
print(engine,"engine of database")
print(Base,"Base")

async def init_db():
    try:
        from src.infrastructure.models.user import UserModel
        from src.infrastructure.models.otp import OTPModel
        from src.infrastructure.models.forgetToken import ForgotPasswordToken
        async with engine.begin() as conn:
            logger.info("Starting table creation...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Tables created successfully!")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session