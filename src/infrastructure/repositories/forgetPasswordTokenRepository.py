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
from sqlalchemy.exc import SQLAlchemyError

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
        try:
            print(f"Checking if user {user_id} can request a new token.")
            
            # Execute query to fetch the last token
            result = await self.session.execute(
                select(ForgotPasswordToken)
                .where(ForgotPasswordToken.user_id == user_id)
                .order_by(ForgotPasswordToken.created_at.desc())
                .limit(1)
            )
            print(result, "Query executed.")

            # Get the last token or None
            last_token = result.scalar_one_or_none()
            
            if not last_token:
                print(f"No token found for user {user_id}, allowing a new token request.")
                return True

            print(f"Last token found: {last_token.id}")

            # Define the minimum interval between requests (e.g., 5 minutes)
            min_interval = timedelta(minutes=5)
            current_time = datetime.now(pytz.utc)
            time_since_last_token = current_time - last_token.created_at
            
            # Check if the interval has passed
            can_request = time_since_last_token > min_interval
            print(f"Time since last token: {time_since_last_token}, can request new token: {can_request}")
            
            return can_request

        except SQLAlchemyError as e:
            print(f"Database error while checking token: {str(e)}")
            return False


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
