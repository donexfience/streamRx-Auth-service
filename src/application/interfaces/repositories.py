from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.entities.user import User

class UserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> User:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    async def delete(self, user_id: int) -> bool:
        pass

    @abstractmethod
    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        pass
    
    @abstractmethod
    async def change_password(self,user_id:int,new_password:str)->None:
        pass
    
    @abstractmethod
    async def updateWithGoogle(self,user_id:int,google_id:str)-> Optional[User]:
        pass