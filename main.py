from contextlib import asynccontextmanager
from redis import Redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy import text
import logging
from typing import Dict, Any
from src.infrastructure.config.reddis_config import RedisConfig
from src.core.config import settings
from src.infrastructure.database.connection import engine, init_db
from src.presentation.api.routes.health import router as health_router
from src.presentation.graphql.schema import graphql_app
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Inspection Utilities
async def get_all_tables() -> list[str]:
    """
    Retrieve all table names in the database.
    
    Returns:
        List[str]: List of table names
    """
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            ))
            tables = [row[0] for row in result.fetchall()]
            return tables
    except Exception as e:
        logger.error(f"Error retrieving tables: {e}")
        return []

async def inspect_columns(table_name: str) -> list[Dict[str, Any]]:
    """
    Inspect columns of a specific table.
    
    Args:
        table_name (str): Name of the table to inspect
    
    Returns:
        List[Dict[str, Any]]: List of column details
    """
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(f"""
                SELECT 
                    column_name, 
                    data_type, 
                    is_nullable, 
                    column_default
                FROM information_schema.columns 
                WHERE table_name = :table_name
                """), 
                {"table_name": table_name}
            )
            columns = [
                {
                    "name": row.column_name,
                    "type": row.data_type,
                    "nullable": row.is_nullable == 'YES',
                    "default": row.column_default
                } 
                for row in result.fetchall()
            ]
            return columns
    except Exception as e:
        logger.error(f"Error inspecting columns for {table_name}: {e}")
        return []

async def full_database_inspection() -> Dict[str, Any]:
    """
    Perform a comprehensive database inspection.
    
    Returns:
        Dict[str, Any]: Detailed database inspection report
    """
    try:
        tables = await get_all_tables()
        table_details = {}
        for table in tables:
            columns = await inspect_columns(table)
            table_details[table] = {
                "column_count": len(columns),
                "columns": columns
            }
        
        logger.info(f"Database Inspection Complete")
        logger.info(f"Total Tables Found: {len(tables)}")
        
        return {
            "total_tables": len(tables),
            "tables": table_details
        }
    
    except Exception as e:
        logger.error(f"Database inspection failed: {e}")
        return {
            "error": str(e),
            "total_tables": 0,
            "tables": {}
        }

# Redis client
redis_client: Redis | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    global redis_client

    try:
        await init_db()
        inspection_result = await full_database_inspection()
        logger.info(f"Database Inspection Result: {inspection_result}")
        redis_client = RedisConfig().get_client()
        try:
            redis_client.ping()
            logger.info("Redis connection successful")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")

        yield 

    except Exception as e:
        logger.error(f"Startup process failed: {e}")
        raise
    
    finally:
        if redis_client:
            redis_client.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(graphql_app, prefix="/graphql")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)