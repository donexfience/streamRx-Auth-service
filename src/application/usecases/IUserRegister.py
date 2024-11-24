
from datetime import datetime
import random
import string
from redis import Redis
from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.infrastructure.repositories.otp_repository import SQLAlchemyOTPRepository
from src.application.usecases.IEmailUseCase import EmailServiceUseCase
from src.application.usecases.ItokenUseCases import TokenServiceUseCase
from src.application.services.password_service import PasswordServiceUseCase

class UserRegistrationServiceUseCase:
    def __init__(
        self,
        user_repository,
        otp_repository: SQLAlchemyOTPRepository,
        email_service: EmailServiceUseCase,
        redis_client: Redis
    ):
        self.user_repository = user_repository
        self.otp_repository = otp_repository
        self.email_service = email_service
        self.redis_client = redis_client
        self.token_service = TokenServiceUseCase()
        self.password_service = PasswordServiceUseCase()
        
    def generate_otp(self) -> str:
        return ''.join(random.choices(string.digits, k=6))

    async def initiate_registration(self, email: str, password: str, is_superuser: bool = False) -> dict:
        existing_user = await self.user_repository.get_by_email(email)
        if existing_user:
            raise ValueError("User with this email already exists")
        otp = self.generate_otp()
        await self.otp_repository.create(email, otp)

        # Cache registration data in Redis for session handling
        registration_data = {
            "email": email,
            "password": password,
            "is_superuser": str(is_superuser)
        }
        self.redis_client.hmset(f"registration:{email}", registration_data)
        self.redis_client.expire(f"registration:{email}", 1800)  # 30 minutes expiry

        # Send verification email
        await self.email_service.send_verification_email(email, otp)

        return {"message": "Registration initiated. Please verify your email."}

    async def verify_otp(self, email: str, otp: str) -> tuple[User, str]:
        # Get OTP from database
        stored_otp = await self.otp_repository.get_by_email(email)
        if not stored_otp:
            raise ValueError("No OTP found for this email")

        if stored_otp.is_expired:
            raise ValueError("OTP has expired")

        if stored_otp.attempts >= 3:
            raise ValueError("Maximum verification attempts exceeded")

        if stored_otp.code != otp:
            await self.otp_repository.update_attempts(stored_otp.id)
            raise ValueError("Invalid OTP")

        # Get cached registration data from Redis
        registration_key = f"registration:{email}"
        cached_data = self.redis_client.hgetall(registration_key)
        
        if not cached_data:
            # If no cached data, check if it's a resend verification
            stored_otp = await self.otp_repository.get_by_email(email)
            if not stored_otp:
                raise ValueError("Registration session expired")

        # Create user
        user_data = cached_data or {}  # Use cached data if available
        user = User(
            email=Email(email),
            hashed_password=self.password_service.get_password_hash(user_data.get(b"password", b"").decode()),
            is_superuser=user_data.get(b"is_superuser", b"False").decode() == "True"
        )
        
        created_user = await self.user_repository.create(user)
        
        # Mark OTP as verified
        await self.otp_repository.mark_as_verified(stored_otp.id)
        
        access_token = self.token_service.create_access_token({"sub": str(created_user.id)})
        
        # Clean up Redis cache
        self.redis_client.delete(registration_key)
        
        return created_user, access_token

    async def resend_otp(self, email: str) -> dict:
        # Check Redis for ongoing registration
        registration_key = f"registration:{email}"
        cached_data = self.redis_client.hgetall(registration_key)
        
        if not cached_data:
            raise ValueError("No ongoing registration found")

        # Check if previous OTP exists and delete it
        existing_otp = await self.otp_repository.get_by_email(email)
        if existing_otp and existing_otp.attempts >= 3:
            raise ValueError("Maximum resend attempts reached")

        # Generate and store new OTP
        new_otp = self.generate_otp()
        await self.otp_repository.create(email, new_otp)
        
        # Send new verification email
        await self.email_service.send_verification_email(email, new_otp)
        
        return {"message": "New OTP sent"}