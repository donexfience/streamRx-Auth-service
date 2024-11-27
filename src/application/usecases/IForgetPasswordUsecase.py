from src.application.interfaces.forgetPasToken import IForgotPasswordTokenRepository
from src.application.usecases.IEmailUseCase import EmailServiceUseCase
from datetime import datetime

class ForgotPasswordUseCase:
    def __init__(self, token_repository: IForgotPasswordTokenRepository, email_service: EmailServiceUseCase):
        self.token_repository = token_repository
        self.email_service = email_service
    
    async def request_password_reset(self, user_id: int, email: str) -> str:
        print(f"Checking reset eligibility for user {user_id}.")
        
        if not await self.token_repository.can_request_new_token(user_id):
            raise Exception("Please wait before requesting another reset link.")
        
        print("User is eligible to request a new token.")
        
        # Create a new token
        token = await self.token_repository.create_token(user_id)
        print(f"Generated new token: {token.token}")

        # Generate the reset link
        reset_link = f"https://yourfrontend.com/forgot-password?token={token.token}"
        
        # Send email with the reset link
        await self.email_service.send_password_change_email(email, reset_link)
        print(f"Reset link sent to {email}.")
        
        return reset_link


    async def verify_token(self, token: str) -> bool:
        # Get the token
        stored_token = await self.token_repository.get_token(token)
        if not stored_token or stored_token.is_used or stored_token.expires_at < datetime.utcnow():
            return False

        return True

    async def mark_token_used(self, token: str):
        await self.token_repository.mark_token_used(token)
