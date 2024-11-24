from datetime import datetime
from dataclasses import dataclass

@dataclass
class OTP:
    id: int
    user_email: str
    code: str
    created_at: datetime
    attempts: int = 0
    is_verified: bool = False
    
    
@property
def is_expired(self) -> bool:
    return (datetime.utcnow() - self.created_at).seconds > 180 