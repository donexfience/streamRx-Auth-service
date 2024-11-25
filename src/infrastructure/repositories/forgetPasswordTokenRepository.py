from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from typing import Optional
import uuid
from datetime import datetime, timedelta
from src.infrastructure.models.forgetToken import ForgotPasswordToken
from src.application.interfaces.forgetPasToken import IForgotPasswordTokenRepository

class ForgotPasswordTokenRepository(IForgotPasswordTokenRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_token(self, user_id: int) -> ForgotPasswordToken:
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
