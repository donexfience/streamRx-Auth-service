from typing import Dict, Optional
from fastapi import HTTPException, status

class BlockorUnblockUseCase:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    async def block_or_unblock(self, email: str, value: bool) -> Dict:
        print(f"email here with value: {email}, {value}")
        # First check if user exists
        user = await self.user_repository.get_by_email(email)
        if not user:
            raise ValueError(f"User with email {email} does not exist")

        # Attempt to block/unblock
        updated_user = await self.user_repository.blockOrUnblock(email, value)
        if not updated_user:
            raise ValueError(f"Failed to update status for user with email {email}")

        return {
            "email": updated_user.email,
            "status": "blocked" if not updated_user.is_active else "unblocked"
        }   