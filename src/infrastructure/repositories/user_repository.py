from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.application.interfaces.repositories import UserRepository
from src.infrastructure.models.user import UserModel
from datetime import datetime,date
from src.application.services.password_service import PasswordServiceUseCase

class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
        self.passwordService = PasswordServiceUseCase()

    def _map_to_entity(self, model: UserModel) -> User:
        return User(
            id=model.id,
            email=Email(model.email),
            hashed_password=model.hashed_password,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            username=model.username,
            date_of_birth=model.date_of_birth,
            phone_number=model.phone_number
            
        )

    def _map_to_model(self, entity: User) -> UserModel:
        return UserModel(
            id=entity.id,
            email=str(entity.email),
            hashed_password=entity.hashed_password,
            is_active=entity.is_active,
            username=entity.username,
            date_of_birth=entity.date_of_birth if isinstance(entity.date_of_birth, datetime) else datetime.strptime(entity.date_of_birth, '%Y-%m-%d'),
            phone_number=entity.phone_number
        )

    async def create(self, user: User) -> User:
        if self.session is None:
            raise ValueError("session is not initialized")
        user_model = self._map_to_model(user)
        self.session.add(user_model)
        print(user_model,"user in the repositoryyyyyyyyyyyyyyyyyyyyyy")
        await self.session.commit()
        await self.session.refresh(user_model)
        return self._map_to_entity(user_model)

    async def get_by_id(self, user_id: int) -> Optional[User]:
        print(user_id,"in the repo user get byid")
        result = await self.session.execute(
            select(UserModel).filter(UserModel.id == user_id)
        )
        print(result,"user got broooooooooooooooooooooooooo")
        user_model = result.scalar_one_or_none()
        return self._map_to_entity(user_model) if user_model else None

    async def get_by_email(self, email: str) -> Optional[User]:
        print(email,"in the getbyemail alchemyrepository",self.session)
        result = await self.session.execute(
            select(UserModel).filter(UserModel.email == email)
        )
        user_model = result.scalar_one_or_none()
        return self._map_to_entity(user_model) if user_model else None

    async def updateWithGoogle(self,user_id:int,google_id:str) -> Optional[User]:
        if not user_id:
            return None
        
        result = await self.session.execute(
            select(UserModel).filter(UserModel.id == user_id)
        )
        user_model = result.scalar_one_or_none()
        
        if not user_model:
            return None
        user_model.google_id = google_id

        await self.session.commit()
        await self.session.refresh(user_model)
        return self._map_to_entity(user_model)

    async def delete(self, user_id: int) -> bool:
        result = await self.session.execute(
            select(UserModel).filter(UserModel.id == user_id)
        )
        user_model = result.scalar_one_or_none()
        
        if not user_model:
            return False

        await self.session.delete(user_model)
        await self.session.commit()
        return True

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        result = await self.session.execute(
            select(UserModel)
            .offset(skip)
            .limit(limit)
        )
        user_models = result.scalars().all()
        return [self._map_to_entity(user_model) for user_model in user_models]

    async def change_password(self, user_id: int, new_password: str) -> None:
        try:
            query = select(UserModel).where(UserModel.id == user_id)
            result = await self.session.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                raise ValueError(f"User with ID {user_id} not found")

            # Hash and update the user's password
            hashed_password = self.passwordService.get_password_hash(new_password)
            user.hashed_password = hashed_password
            
            await self.session.commit()
            print(f"Password updated successfully for user: {user_id}")

        except Exception as e:
            await self.session.rollback()
            print("Error in change_password:", str(e))
            raise


        