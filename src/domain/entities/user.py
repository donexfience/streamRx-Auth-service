from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from src.domain.value_objects.email import Email
from src.__lib.UserRole import UserRole

@dataclass
class User:
    email: Email  
    hashed_password: Optional[str]  =None
    id: Optional[int] = None  
    profileImageURL: Optional[str] = None  
    is_verified: bool = False  
    bio: Optional[str] = None 
    role: UserRole = UserRole.VIEWER  
    is_active: bool = True 
    google_id: Optional[str] = None 
    created_at: datetime = field(default_factory=datetime.utcnow)  
    updated_at: datetime = field(default_factory=datetime.utcnow)  

    @property
    def is_authenticated(self) -> bool:
        """Determines if the user is authenticated."""
        return self.id is not None and self.is_active

    @property
    def is_streamer(self) -> bool:
        """Checks if the user has a streamer role."""
        return self.role == UserRole.STREAMER

    @property
    def is_admin(self) -> bool:
        """Checks if the user has an admin role."""
        return self.role == UserRole.ADMIN

    @property
    def is_moderator(self) -> bool:
        """Checks if the user has a moderator role."""
        return self.role == UserRole.MODERATOR
