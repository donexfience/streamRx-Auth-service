from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.application.interfaces.repositories import UserRepository
from src.infrastructure.models.user import UserModel

class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _map_to_entity(self, model: UserModel) -> User:
        return User(
            id=model.id,
            email=Email(model.email),
            hashed_password=model.hashed_password,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _map_to_model(self, entity: User) -> UserModel:
        return UserModel(
            id=entity.id,
            email=str(entity.email),
            hashed_password=entity.hashed_password,
            is_active=entity.is_active,
        )

    async def create(self, user: User) -> User:
        if self.session is None:
            raise ValueError("session is not initialized")
        user_model = self._map_to_model(user)
        self.session.add(user_model)
        await self.session.commit()
        await self.session.refresh(user_model)
        return self._map_to_entity(user_model)

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(UserModel).filter(UserModel.id == user_id)
        )
        user_model = result.scalar_one_or_none()
        return self._map_to_entity(user_model) if user_model else None

    async def get_by_email(self, email: str) -> Optional[User]:
        print(email,"in the getbyemail alchemyrepository",self.session)
        result = await self.session.execute(
            select(UserModel).filter(UserModel.email == email)
        )
        user_model = result.scalar_one_or_none()
        return self._map_to_entity(user_model) if user_model else None

    async def update(self, user: User) -> Optional[User]:
        if not user.id:
            return None
        
        result = await self.session.execute(
            select(UserModel).filter(UserModel.id == user.id)
        )
        user_model = result.scalar_one_or_none()
        
        if not user_model:
            return None

        user_model.email = str(user.email)
        user_model.hashed_password = user.hashed_password
        user_model.is_active = user.is_active
        user_model.is_superuser = user.is_superuser

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