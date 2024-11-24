from sqlalchemy import Column,Integer,String,DateTime,Boolean,ForeignKey
from src.infrastructure.database.connection import Base
from datetime import datetime

class OTPModel(Base):
    __tablename__ ='otps'
    id=Column(Integer,primary_key=True,index=True)
    user_email = Column(String,index=True)
    code = Column(String)
    created_at =Column(DateTime,default=datetime.utcnow)
    attempts = Column(Integer,default=0)
    is_verified = Column(Boolean,default=False)