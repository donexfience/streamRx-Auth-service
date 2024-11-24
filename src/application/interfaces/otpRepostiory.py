from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime
from src.domain.entities.otp import OTP

class OTPRepository(ABC):
    @abstractmethod
    async def create(self, user_email: str, code: str) -> OTP:
        """Create a new OTP and associate it with an email."""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[OTP]:
        """Retrieve an OTP associated with an email."""
        pass

    @abstractmethod
    async def delete_existing_otps(self, email: str) -> None:
        """Delete existing OTPs for the given email."""
        pass

    @abstractmethod
    async def update_attempts(self, otp_id: int) -> None:
        """Increment the attempt count for an OTP."""
        pass

    @abstractmethod
    async def mark_as_verified(self, otp_id: int) -> None:
        """Mark an OTP as verified."""
        pass
