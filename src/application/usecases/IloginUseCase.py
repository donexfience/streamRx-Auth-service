from datetime import datetime, timedelta
import random
import string
from redis import Redis
from typing import Optional, Dict, Tuple
from src.domain.entities.user import User
from src.infrastructure.repositories.otp_repository import SQLAlchemyOTPRepository
from src.application.usecases.IEmailUseCase import EmailServiceUseCase
from src.application.usecases.ItokenUseCases import TokenServiceUseCase
from src.application.services.password_service import PasswordServiceUseCase
from src.__lib.UserRole import UserRole
from src.domain.value_objects.email import Email
class LoginUseCase:
    def __init__(
        self,
        user_repository,
    ):
        self.user_repository = user_repository
        self.password_service = PasswordServiceUseCase()
        self.token_service  = TokenServiceUseCase()

    async def Login(self,email:str,password:str)->Dict :
        print('user in the login')
        email_obj =str(email)
        user:Optional[User] = await self.user_repository.get_by_email(email_obj)
        print(user,"userrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr")
        if not user:
            return {
                "success":False,
                "message":"user not found"
            }
        
        if not self.password_service.verify_password(password, user.hashed_password):
            return {
                "success": False,
                "message": "Invalid password"
            }

        if not user.is_active:
            return {
                "success":False,
                "message":"your accound is blocked Please contact support."
            }
            
        if user.role.value =='streamer':
            return {
                "success":False,
                "message":"Go to stremaer login page"
            }
            
            
        print(user,"User in the loign user casseeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
        
        tokenroles=''
        
        if email == 'naji2@gmail.com':
            tokenroles = 'admin'
        elif user.role.value == 'streamer': 
            tokenroles = 'streamer'
        else:
            tokenroles = 'viewer'

        token_data = {
            "user_id": user.id,
            "role": tokenroles,
            "email":user.email.value
        }
        print(token_data,"token data setting ")
        print(user,"user data")
        access_token = self.token_service.create_access_token(token_data)
        refresh_token = self.token_service.create_refresh_token(token_data)
        return {
            "success": True,
            "message": "Login successful.",
            "user": {
                "id": user.id,
                "email": user.email.value,
                "role": user.role.value,
                "is_verified": user.is_verified,
                "is_active":user.is_active
            },
            "tokens": {
                "access_token": access_token,
                "refresh_token": refresh_token,
            },
        }
    async def StreamerLogin(self,email:str,password:str)->Dict :
        print('user in the login')
        email_obj =str(email)
        user:Optional[User] = await self.user_repository.get_by_email(email_obj)
        print(user,"userrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr")
        if not user:
            return {
                "success":False,
                "message":"user not found"
            }
        
        if not self.password_service.verify_password(password, user.hashed_password):
            return {
                "success": False,
                "message": "Invalid password"
            }

        if not user.is_active:
            return {
                "success":False,
                "message":"your accound is blocked Please contact support."
            }
        if not user.role == 'streamer':
            return{
                "success":False,
                "message":"You cant Login as a Streamer You dont have access"
            }
        print(user,"User in the loign user casseeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
    
        print(user,"user data")
         # making object for storing user data
        
        user_data = {
            "id": str(user.id),
            "email": str(user.email),
            "role": user.role.value,
            "bio": user.bio,
            "is_verified":user.is_verified,
            "profileImageURL": user.profileImageURL,
            "is_active": user.is_active,
            "phone_number": user.phone_number,
            "username": user.username
        }
    
        # Generate access token
        access_token = self.token_service.create_access_token(user_data)
        refresh_token = self.token_service.create_refresh_token(user_data)
        return {
            "success": True,
            "message": "Login successful.",
            "user": {
                "id": user.id,
                "email": user.email.value,
                "role": user.role.value,
                "is_verified": user.is_verified,
                "is_active":user.is_active
            },
            "tokens": {
                "access_token": access_token,
                "refresh_token": refresh_token,
            },
        }