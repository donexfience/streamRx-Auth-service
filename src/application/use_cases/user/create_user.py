from dataclasses import dataclass
from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.application.interfaces.repositories import UserRepository
from src.application.services.password_service import PasswordService
from src.application.services.token_service import TokenService
@dataclass
class CreateUserInput:
    email: str
    password: str
    is_superuser: bool = False

class CreateUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.token_service = TokenService()
        self.password_service = PasswordService()

    async def execute(self, input_data: CreateUserInput) -> User:
        # Check if user already exists
        print(input_data.email,input_data.password,"from usecase class")
        existing_user = await self.user_repository.get_by_email(input_data.email)
        if existing_user:
            raise ValueError("User with this email already exists")
        # Create new user
        user = User(
            email=Email(input_data.email),
            hashed_password=self.password_service.get_password_hash(input_data.password),
            is_superuser=input_data.is_superuser
        )
        
        print(user,"user before saving")
        # Save and return user
        created_user = await self.user_repository.create(user)
        return created_user