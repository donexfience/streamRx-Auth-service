
from src.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from src.__lib.UserRole import UserRole
from src.domain.entities.user import User
from typing import Dict, Optional, Any

class RoleChangeUsecase:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    async def RoleChange(self, email: str, role: str) -> Dict:
        print('email got ', email)
        email_obj = str(email)
        user: Optional[User] = await self.user_repository.get_by_email(email_obj)
        print('user got', user)
        
        if not user:
            return {
                "success": False,  
                "message": "User not found",
                "user": None
            }
        try:
            new_role = UserRole[role.upper()]
        except KeyError:
            valid_roles = ", ".join([r.name for r in UserRole])
            raise ValueError(f"Invalid role. Valid roles are: {valid_roles}")

        
        user.role = new_role
        await self.user_repository.update_user(user)
        print(f"Database user updated successfully: {user.id} with role {role}")
        return {
            "success": True, 
            "message": "Role changed successfully.",
            "user": {
                "email": user.email.value,
                "role": user.role.value,
                "id": user.id,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                
            }
        }
