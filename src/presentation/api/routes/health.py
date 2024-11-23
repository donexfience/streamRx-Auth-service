from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database.connection import get_session

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(session: AsyncSession = Depends(get_session)):
    """
    Health check endpoint to verify API and database status
    """
    try:
        # Test database connection
        await session.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = "unhealthy"
        
    return {
        "status": "ok",
        "api_version": "1.0.0",
        "database": {
            "status": db_status
        },
        "services": {
            "api": "healthy",
            "graphql": "healthy"
        }
    }