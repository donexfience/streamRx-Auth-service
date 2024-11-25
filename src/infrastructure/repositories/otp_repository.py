from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entities.otp import OTP
from src.application.interfaces.otpRepostiory import OTPRepository
from src.infrastructure.models.otp import OTPModel
from datetime import datetime
from sqlalchemy import select,delete
from typing import Optional

class SQLAlchemyOTPRepository(OTPRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    async def create(self,user_email:str,code:str)->OTP :
        await self.delete_existing_otps(user_email)
        otp_model = OTPModel(
            user_email = user_email,
            code = code,
            created_at =datetime.utcnow()
        )
        self.session.add(otp_model)
        await self.session.commit()
        await self.session.refresh(otp_model)
        return OTP(
            id=otp_model.id,
            user_email=otp_model.user_email,
            code=otp_model.code,
            created_at=otp_model.created_at,
            attempts=otp_model.attempts,
            is_verified=otp_model.is_verified,
            is_expired =otp_model.is_expired
        )
        
    async def get_by_email(self, email: str) -> Optional[OTP]:
        result = await self.session.execute(
            select(OTPModel).where(OTPModel.user_email == email)
        )
        otp_model = result.scalar_one_or_none()
        
        if otp_model:
            return OTP(
                id=otp_model.id,
                user_email=otp_model.user_email,
                code=otp_model.code,
                created_at=otp_model.created_at,
                attempts=otp_model.attempts,
                is_verified=otp_model.is_verified,
                is_expired = otp_model.is_expired
            )
        return None    
    async def delete_existing_otps(self, email: str) -> None:
        await self.session.execute(
            delete(OTPModel).where(OTPModel.user_email == email)
        )
        await self.session.commit()

    async def update_attempts(self, otp_id: int) -> None:
        result = await self.session.execute(
            select(OTPModel).where(OTPModel.id == otp_id)
        )
        otp_model = result.scalar_one_or_none()
        if otp_model:
            otp_model.attempts += 1
            await self.session.commit()
    async def delete_otp_by_id(self,otp_id:int)->None:
        await self.session.execute(delete(OTPModel).where(OTPModel.id==otp_id))
        await self.session.commit()
        
    async def mark_as_verified(self, otp_id: int) -> None:
        result = await self.session.execute(
            select(OTPModel).where(OTPModel.id == otp_id)
        )
        otp_model = result.scalar_one_or_none()
        if otp_model:
            otp_model.is_verified = True
            await self.session.commit()