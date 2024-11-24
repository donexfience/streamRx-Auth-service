from datetime import datetime
import random
import string
from redis import Redis
from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.infrastructure.repositories.otp_repository import SQLAlchemyOTPRepository
from src.application.interfaces.repositories import UserRepository
from src.application.services.token_service import TokenService
from src.application.services.password_service import PasswordService
from src.infrastructure.repositories.user_repository import SQLAlchemyUserRepository

class RegisterationService:
    def __init__(self):
        self,
        user_repository : SQLAlchemyUserRepository
        otp_respository : SQLAlchemyOTPRepository
        email_service : Email_service
        self.redis_cient = redis_client
        
        otp 
