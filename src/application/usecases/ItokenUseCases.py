
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict
from jose import jwt, JWTError
from fastapi import HTTPException, status
from passlib.context import CryptContext
from src.core.config import settings

class TokenServiceUseCase:
    @staticmethod
    def create_access_token(data: dict) -> str:
        """Create access token with 2 minutes expiration"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=2)
        to_encode.update({
            "exp": expire,
            "token_type": "access"
        })
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    @staticmethod
    def create_refresh_token(data:dict)->str:
        """Create refresh token with 7 days expiration"""
        to_encode = data.copy()
        expire =datetime.utcnow() + timedelta(days=7)
        to_encode.update({
            "exp":expire,
            "token_type":"refresh"
        })
        return jwt.encode(to_encode,settings.SECRET_KEY,algorithm=settings.JWT_ALGORITHM)
    @staticmethod
    def decode_token(token: str) -> Dict:
        """Decode and verify token, raising appropriate exceptions"""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    def verify_session(access_token: Optional[str] = None) -> Dict:
        """Verify access token and return payload or raise appropriate exception"""
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        try:
            payload = TokenServiceUseCase.decode_token(access_token)
            if payload.get("token_type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return payload
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )