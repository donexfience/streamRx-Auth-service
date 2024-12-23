from src.domain.entities.user import User
from typing import List,Optional

class GetAllUsersUseCase:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    async def execute(self) -> List[User]:
        print("Executing GetAllUsersUseCase")
        try:
            users = await self.user_repository.get_all_users()
            return users
        except Exception as e:
            print(f"Error in GetAllUsersUseCase: {e}")
            return []
