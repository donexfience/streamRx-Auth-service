
from sqlalchemy import Boolean, Column, Integer, String, DateTime,Text,Date
from sqlalchemy.sql import func
from sqlalchemy import Enum as SQLAlchemyEnum  
from src.infrastructure.database.connection import Base
from src.__lib.UserRole import UserRole

class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    username = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)  
    date_of_birth = Column(Date, nullable=True) 
    profileImageURL  = Column(String, nullable=True)
    bio = Column(Text,nullable=True)
    social_links=Column(String,nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified=Column(Boolean,nullable=False,default=True)
    role = Column(SQLAlchemyEnum(UserRole), nullable=False, default=UserRole.VIEWER)  
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    google_id = Column(String,nullable=True)
    
