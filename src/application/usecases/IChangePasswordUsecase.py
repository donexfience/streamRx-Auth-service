
from src.application.services.password_service import PasswordServiceUseCase
from src.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from src.infrastructure.repositories.forgetPasswordTokenRepository import ForgotPasswordTokenRepository

class ChangePasswordUseCase:
    def __init__(self, user_repository: SQLAlchemyUserRepository, password_service: PasswordServiceUseCase,forgotTokenRepository:ForgotPasswordTokenRepository):
        self.user_repository = user_repository
        self.forgot_otp_repository = forgotTokenRepository
        self.password_service = password_service

    async def execute(self, user_id: int, token:str, new_password: str) -> str:
        print('here in usecase of change passsword',user_id)
        user = await self.user_repository.get_by_id(user_id)
        print(user,"user found")
        token = await self.forgot_otp_repository.get_valid_token_for_user(user.id)
        print(token,"token kitti")
        if not token:
            raise ValueError("Token not found")
        if not user:
            raise ValueError("User not found")
        await self.user_repository.change_password(user_id, new_password)
        return "Password changed successfully"