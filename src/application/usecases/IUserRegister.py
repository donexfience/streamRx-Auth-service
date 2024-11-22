from datetime import datetime, timedelta
import random
import string
from redis import Redis
from typing import Optional, Dict, Tuple
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

    async def get_registration_status(self, email: str) -> Dict:
        """Check if there's an ongoing registration and return its status"""
        registration_key = f"registration:{email}"
        cached_data = self.redis_client.hgetall(registration_key)
        
        if not cached_data:
            return {
                "status": "no_registration",
                "message": "No ongoing registration found"
            }
            
        stored_otp = await self.otp_repository.get_by_email(email)
        if not stored_otp:
            # Clean up orphaned registration data
            self.redis_client.delete(registration_key)
            return {
                "status": "no_registration",
                "message": "No ongoing registration found"
            }

        # Calculate time remaining
        expiry_time = stored_otp.created_at + timedelta(minutes=30)
        time_remaining = int((expiry_time - datetime.utcnow()).total_seconds())
        
        if time_remaining <= 0 or stored_otp.is_expired:
            await self._cleanup_registration(email)
            return {
                "status": "expired",
                "message": "Registration expired. Please start again."
            }

        if stored_otp.is_verified:
            return {
                "status": "verified",
                "message": "Email already verified"
            }

        if stored_otp.attempts >= 3:
            return {
                "status": "max_attempts_reached",
                "message": "Maximum verification attempts reached"
            }
            
        return {
            "status": "pending_verification",
            "message": "OTP verification pending",
            "email": email,
            "created_at": stored_otp.created_at.isoformat(),
            "attempts_remaining": 3 - stored_otp.attempts,
            "expires_in": time_remaining
        }

    async def _cleanup_registration(self, email: str):
        """Clean up registration data from Redis and OTP from database"""
        registration_key = f"registration:{email}"
        self.redis_client.delete(registration_key)
        stored_otp = await self.otp_repository.get_by_email(email)
        if stored_otp:
            await self.otp_repository.delete(stored_otp.id)

    async def initiate_registration(self, email: str, password: str, is_superuser: bool = False) -> Dict:
        # First check if there's an ongoing valid registration
        status = await self.get_registration_status(email)
        
        if status["status"] == "pending_verification":
            return {
                "message": "Registration already initiated",
                "status": status
            }
            
        # Check if user exists
        existing_user = await self.user_repository.get_by_email(email)
        if existing_user:
            raise ValueError("User with this email already exists")

        # Clean up any existing registration data
        await self._cleanup_registration(email)

        # Generate and store new OTP
        otp = self.generate_otp()
        await self.otp_repository.create(email, otp)

        # Cache registration data in Redis
        registration_data = {
            "email": email,
            "password": self.password_service.get_password_hash(password),  # Store hashed password
            "is_superuser": str(is_superuser),
            "initiated_at": datetime.utcnow().isoformat()
        }
        self.redis_client.hmset(f"registration:{email}", registration_data)
        self.redis_client.expire(f"registration:{email}", 1800)  # 30 minutes

        # Send verification email
        await self.email_service.send_verification_email(email, otp)

        status = await self.get_registration_status(email)
        return {
            "message": "Registration initiated. Please verify your email.",
            "status": status
        }

    async def verify_otp(self, email: str, otp: str) -> Tuple[User, str]:
        # First check registration status
        status = await self.get_registration_status(email)
        
        if status["status"] != "pending_verification":
            raise ValueError(status["message"])

        # Get OTP from database
        stored_otp = await self.otp_repository.get_by_email(email)
        if stored_otp.code != otp:
            await self.otp_repository.update_attempts(stored_otp.id)
            raise ValueError("Invalid OTP")

        # Get cached registration data from Redis
        registration_key = f"registration:{email}"
        cached_data = self.redis_client.hgetall(registration_key)
        
        if not cached_data:
            raise ValueError("Registration session expired")

        # Create user
        user = User(
            email=Email(email),
            hashed_password=cached_data.get(b"password", b"").decode(),  # Password is already hashed
            is_superuser=cached_data.get(b"is_superuser", b"False").decode() == "True"
        )
        
        created_user = await self.user_repository.create(user)
        
        # Mark OTP as verified
        await self.otp_repository.mark_as_verified(stored_otp.id)
        
        # Generate access token
        access_token = self.token_service.create_access_token({"sub": str(created_user.id)})
        
        # Clean up Redis cache
        await self._cleanup_registration(email)
        
        return created_user, access_token

    async def resend_otp(self, email: str) -> Dict:
        # Check registration status
        status = await self.get_registration_status(email)
        
        if status["status"] != "pending_verification":
            raise ValueError(status["message"])

        # Generate and store new OTP
        new_otp = self.generate_otp()
        stored_otp = await self.otp_repository.get_by_email(email)
        
        if stored_otp:
            await self.otp_repository.delete(stored_otp.id)
            
        await self.otp_repository.create(email, new_otp)
        
        # Send new verification email
        await self.email_service.send_verification_email(email, new_otp)
        
        # Get updated status
        new_status = await self.get_registration_status(email)
        return {
            "message": "New OTP sent",
            "status": new_status
        }