from enum import Enum
from sqlalchemy import Enum as SQLAlchemyEnum

class UserRole(Enum):
    STREAMER = "streamer"
    VIEWER = "viewer"
    EDITOR ="editor"
    MODERATOR = "moderator"
    ADMIN = "admin"