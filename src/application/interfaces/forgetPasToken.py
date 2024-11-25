from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

class IForgotPasswordTokenRepository(ABC):
    @abstractmethod
    async def create_token(self, user_id: int) -> str:
        """Creates a forgot password token for a user."""
        pass

    @abstractmethod
    async def get_token(self, token: str) -> Optional[str]:
        """Fetches a token by its value."""
        pass

    @abstractmethod
    async def mark_token_used(self, token: str):
        """Marks a token as used."""
        pass
