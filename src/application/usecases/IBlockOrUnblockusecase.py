from src.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from typing import Dict, Optional
from fastapi import HTTPException, status

class BlockorUnblockUseCase:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    async def block_or_unblock(self, email: str ,value:bool) -> Dict:
        user = await self.user_repository.find_by_email(email)
        if not user:
            raise ValueError(f"User with email {email} does not exist")

        user = await self.user_repository.blockOrUnblock(email,value)
        return {
            "email": user.email,
            "status": "blocked" if user.is_blocked else "unblocked"
        }