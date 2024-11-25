from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ForgotPasswordToken(Base):
    __tablename__ = "forgot_password_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts_remaining = Column(Integer, default=3)
    is_used = Column(Boolean, default=False)
