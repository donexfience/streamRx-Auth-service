from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from src.core.config import settings
import logging
import os



DATABASE_URL = os.environ.get('DATABASE_URL')
print(DATABASE_URL,"database url in the connection")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
engine = create_async_engine(DATABASE_URL, echo=True,pool_pre_ping=True,pool_recycle=3600)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


logging.debug(f"Database URL: {engine.url}")
print(engine,"engine of database")
print(Base,"Base")

async def verify_db_connection():
    try:
        async with engine.connect() as conn:
            result = await conn.execute("SELECT 1")
            logger.info("Database connection successful!")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

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
        logger.error(f"Detailed error creating tables: {e}")
        import traceback
        traceback.print_exc()

async def get_session() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Session error: {e}")
            await session.rollback()
        finally:
            await session.close()