from pydantic import BaseModel, EmailStr 
from typing import Optional
from datetime import date
from src.__lib.UserRole import UserRole

class UpdateUserDTO(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    hashed_password:Optional[str]=None
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    profileImageURL: Optional[str] = None
    is_verified: Optional[bool] = None
    bio: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    google_id: Optional[str] = None
