from typing import Optional
from src.domain.entities.user import User
from src.domain.dto.updateUserDTO import UpdateUserDTO
from src.infrastructure.repositories.user_repository import UserRepository
from datetime import datetime

class UpdateUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

class UpdateUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, email: str, update_data: UpdateUserDTO) -> User:
        existing_user = await self.user_repository.get_by_email(email)
        if not existing_user:
            raise ValueError("user with email already exist")
        print(existing_user,'exisitinig user ')
        print(update_data,"data to updatedddddddddddd")
        updated_user = User(
            email=existing_user.email,  
            hashed_password=existing_user.hashed_password,  
            id=existing_user.id,
            username=update_data.username or existing_user.username,
            phone_number=update_data.phone_number or existing_user.phone_number,
            date_of_birth=update_data.date_of_birth or existing_user.date_of_birth,
            profileImageURL=update_data.profileImageURL or existing_user.profileImageURL,
            is_verified=update_data.is_verified if update_data.is_verified is not None else existing_user.is_verified,
            bio=update_data.bio or existing_user.bio,
            role=update_data.role or existing_user.role,
            is_active=update_data.is_active if update_data.is_active is not None else existing_user.is_active,
            google_id=update_data.google_id or existing_user.google_id,
            created_at=existing_user.created_at, 
            updated_at=datetime.utcnow(),  
            social_links=update_data.social_links or existing_user.social_links,
        )
        saved_user = await self.user_repository.update_user(updated_user)
        print(saved_user,"updated user in the usecase")
        return saved_user
