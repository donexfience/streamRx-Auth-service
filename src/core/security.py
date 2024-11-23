from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
from src.core.config import settings

def verify_password(plain_password:str,hashed_password:str)->bool:
    return pwd_context.verify(plain_password,hashed_password)

def get_password_hash(password:str)->str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """create access token for 2 mins"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=2)
    to_encode.update({
        "exp":expire,
        "token_type":"access"
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(data:dict)->str:
    """create refresh token for 7 days"""
    to_encode = data.copy();
    expire = datetime.utcnow()+timedelta(days=7)
    to_encode.update(
        {
            "exp":expire,
            "token_type":"refresh"
        }
    )
    encoded_jwt = jwt.encode(to_encode,settings.SECRET_KEY,algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt
def create_tokens(user_id:int)->tuple[str,str]:
    """create both access and refresh token"""
    token_data={"sub":str(user_id)}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    return access_token , refresh_token

def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """
    Verify a token and return its payload if valid
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Verify token type
        if payload.get("token_type") != token_type:
            return None
            
        return payload
    except JWTError:
        return None

def refresh_access_token(refresh_token: str) -> Optional[str]:
    """
    Create a new access token using a valid refresh token
    """
    payload = verify_token(refresh_token, token_type="refresh")
    if not payload:
        return None
        
    # Create new access token with same user ID
    user_id = payload.get("sub")
    if not user_id:
        return None
        
    return create_access_token({"sub": user_id})