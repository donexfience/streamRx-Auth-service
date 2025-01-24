from src.domain.entities.user import User
from typing import List,Optional
from src.infrastructure.models.user import UserModel

class GetUserByIdUseCase:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    async def execute(self,email:str) -> User:
        print("Executing GetAllUsersUseCase")
        try:
            users = await self.user_repository.get_by_email(email)
            if not users:
                print("No users found")
                return []
            return users
        except Exception as e:
            print(f"Error in GetAllUsersUseCase: {e}")
            raise e  