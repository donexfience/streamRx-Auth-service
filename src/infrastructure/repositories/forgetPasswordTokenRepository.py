from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from typing import Optional
import uuid
from datetime import datetime, timedelta
from src.infrastructure.models.forgetToken import ForgotPasswordToken
from src.application.interfaces.forgetPasToken import IForgotPasswordTokenRepository
from datetime import datetime
import pytz

class ForgotPasswordTokenRepository(IForgotPasswordTokenRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_valid_token_for_user(self,user_id:int):
        
        now = datetime.now()
        print("get valid token",now)
        
        token_data = await self.session.execute(
            select(ForgotPasswordToken)
            .where(
                ForgotPasswordToken.user_id == user_id,
                ForgotPasswordToken.is_used == False,
                ForgotPasswordToken.expires_at > now,
                ForgotPasswordToken.attempts_remaining <= 3
            ).order_by(ForgotPasswordToken.created_at.desc()).limit(1)
        )
        print('kkkkkkkkkkkkkkkk')
        print(token_data.scalar_one_or_none,"data in the get valid token")
        return token_data.scalar_one_or_none()
    
    async def create_token(self, user_id: int) -> ForgotPasswordToken:
        print('hello')
        existing_token = await self.get_valid_token_for_user(user_id)
        print(existing_token)
        if existing_token:
            return existing_token
        token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        forgot_password_token = ForgotPasswordToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            attempts_remaining=3,
            is_used=False,
        )
        self.session.add(forgot_password_token)
        await self.session.commit()
        return forgot_password_token
    
    async def can_request_new_token(self, user_id: int) -> bool:
        print(f"Checking if user {user_id} can request a new token.")
        
        result = await self.session.execute(
            select(ForgotPasswordToken)
            .where(ForgotPasswordToken.user_id == user_id)
            .order_by(ForgotPasswordToken.created_at.desc())
            .limit(1)
        )
        
        last_token = result.scalar_one_or_none()  # This will give None if no token exists
        
        print(f"Last token: {last_token.id}")
        
        # If no token exists, return True, allowing a new token to be requested
        if not last_token:
            print(f"No token found for user {user_id}, allowing a new token request.")
            return True
        
        # Define the minimum interval between requests (5 minutes)
        min_interval = timedelta(minutes=5)
        
        print('min intervel:', min_interval)
        # Calculate the time difference between the current time and the last token creation time
        current_time = datetime.now(pytz.utc)
        print('current time:', current_time)
        print('old time from DB:', last_token.created_at)
        time_since_last_token = datetime.now(pytz.utc) - last_token.created_at
        # print('Time L:', time_since_last_token)
        
        # Return if enough time has passed (greater than the min interval)
        can_request = time_since_last_token > min_interval
        print(f"Time since last token: {time_since_last_token}, can request new token: {can_request}")
        
        return can_request

    async def get_token(self, token: str) -> Optional[ForgotPasswordToken]:
        query = select(ForgotPasswordToken).where(ForgotPasswordToken.token == token)
        result = await self.session.execute(query)
        try:
            return result.scalar_one()
        except NoResultFound:
            return None

    async def mark_token_used(self, token: str):
        forgot_password_token = await self.get_token(token)
        if forgot_password_token:
            forgot_password_token.is_used = True
            await self.session.commit()
