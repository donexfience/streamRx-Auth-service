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

    @abstractmethod
    async def get_valid_token_for_user(self,user_id:int):
        pass
    
    @abstractmethod
    async def can_request_new_token(self,user_id:int)->bool:
        pass
    
    