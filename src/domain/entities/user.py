from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from src.domain.value_objects.email import Email

@dataclass
class User:
    email: Email  # Non-default argument should come first
    hashed_password: str  # Non-default argument
    id: Optional[int] = None  # Default argument
    
    is_active: bool = True  # Default argument
    is_superuser: bool = False  # Default argument
    created_at: datetime = field(default_factory=datetime.utcnow)  
    updated_at: datetime = field(default_factory=datetime.utcnow)  

    @property
    def is_authenticated(self) -> bool:
        return True if self.id and self.is_active else False
