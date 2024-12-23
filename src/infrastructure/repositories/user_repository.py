from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.application.interfaces.repositories import UserRepository
from src.infrastructure.models.user import UserModel
from datetime import datetime,date
from src.application.services.password_service import PasswordServiceUseCase
import json

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
            phone_number=model.phone_number,
            social_links=model.social_links
            
        )

    def _map_to_model(self, entity: User) -> UserModel:
        return UserModel(
            id=entity.id,
            email=str(entity.email),
            hashed_password=entity.hashed_password,
            is_active=entity.is_active,
            username=entity.username,
            date_of_birth=entity.date_of_birth if isinstance(entity.date_of_birth,datetime) else datetime.strptime(entity.date_of_birth,'%Y-%m-%d') if entity.date_of_birth else None,
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


    async def blockOrUnblock(self,email:str,value:bool)->Optional[User]:
        print('uer in the repo going to block')
        try: 
            result = await self.session.execute(
                select(UserModel).filter(UserModel.email ==email)
            )
            user = result.scalar_one_or_none()
            if not user:
                print("User not found")
                return None
            user.is_blocked = value
            await self.session.commit()
            await self.session.refresh(user)
        
        except Exception as e:
            await self.session.rollback()  
            print(f"Error updating user block status: {e}")
            return None
        
        
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
    
    
    async def get_all_users(self)->List[User]:
        try:
            
            print("in the user repositoroy")
            result = await self.session.execute(select(UserModel))
            users = result.scalars().all()
            return users
        except Exception as e:
           print(f"Error fetching all users: {e}")
           return []
    
        
    async def update_user(self, user: User) -> Optional[User]:
        print(user, "in the repository")
        try:
            if isinstance(user, dict):
                email = user.get('email')
                if not email:
                    raise ValueError("Email is required for user update")
            else:
                email = user.email.value if hasattr(user, 'email') else str(user.email)
            query = select(UserModel).where(UserModel.email == email)
            print(email, "Email being used for update")
            result = await self.session.execute(query)
            db_user = result.scalar_one_or_none()
            print(db_user, "database user") 
            if not db_user:
                return None

            if isinstance(user, dict):
                update_values = user
            else:
                update_values = vars(user)

            for field_name, new_value in update_values.items():
                if field_name in ['id', 'created_at', 'email']:
                    continue
                
                # Handle Email value object
                if isinstance(new_value, Email):
                    new_value = new_value.value 
                
                if field_name == 'social_links':
                    # Serialize social links to JSON string if it's a list of dictionaries
                    if isinstance(new_value, list):
                        try:
                            new_value = json.dumps(new_value)
                        except Exception as e:
                            print(f"Error serializing social links: {e}")
                            continue
                
                # Skip None values to preserve existing data
                if new_value is not None:
                    try:
                        setattr(db_user, field_name, new_value)
                    except AttributeError:
                        print(f"Could not set attribute {field_name}")

            db_user.updated_at = datetime.utcnow()
            
            await self.session.commit()
            await self.session.refresh(db_user)
            print(db_user, "database user updated successfully")
            return self._map_to_entity(db_user)
        except Exception as e:
            await self.session.rollback()
            print("Error in update_user:", str(e))
            raise
                
                    