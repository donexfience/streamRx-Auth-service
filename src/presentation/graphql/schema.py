from typing import List, Optional, Any
from contextlib import asynccontextmanager
from redis import Redis
import strawberry
from strawberry.fastapi import BaseContext, GraphQLRouter
from fastapi import Request
from sqlalchemy.ext.asyncio import async_sessionmaker,AsyncSession
from src.infrastructure.database.connection import async_session
from src.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from src.infrastructure.repositories.otp_repository import SQLAlchemyOTPRepository
from src.application.usecases.IEmailUseCase import EmailServiceUseCase
from src.core.config import settings
from src.application.usecases.IUserRegister import UserRegistrationServiceUseCase
from src.infrastructure.config.reddis_config import RedisConfig

class CustomContext(BaseContext):
    def __init__(self, request: Request):
        super().__init__()
        self.request: Request = request
        self.session: Optional[AsyncSession] = None
        self.redis_client: Optional[Redis] = None
        
    async def __aenter__(self):
        self.session = async_session()
        await self.session.__aenter__()
        # Initialize Redis client
        redis_config = RedisConfig()
        self.redis_client = redis_config.get_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.__aexit__(exc_type, exc_val, exc_tb)
        if self.redis_client:
            self.redis_client.close()

@strawberry.type
class User:
    id: int
    email: str
    is_active: bool
    is_superuser: bool

@strawberry.input
class UserCreateInput:
    email: str
    password: str
    is_superuser: Optional[bool] = False
@strawberry.type
class RegistrationResponse:
    message: str

@strawberry.type
class Query:
    @strawberry.field
    async def users(
        self,
        info,
        skip: int = 0,
        limit: int = 100,
    ) -> List[User]:
        context: CustomContext = info.context
        repository = SQLAlchemyUserRepository(context.session)
        users = await repository.list_users(skip=skip, limit=limit)
        return [
            User(
                id=user.id,
                email=str(user.email),
                is_active=user.is_active,
                is_superuser=user.is_superuser
            )
            for user in users
        ]

    @strawberry.field
    async def user(
        self,
        info,
        user_id: int,
    ) -> Optional[User]:
        context: CustomContext = info.context
        repository = SQLAlchemyUserRepository(context.session)
        user = await repository.get_by_id(user_id)
        if not user:
            return None
        return User(
            id=user.id,
            email=str(user.email),
            is_active=user.is_active,
            is_superuser=user.is_superuser
        )
        
        
@strawberry.type
class Mutation:
    @strawberry.mutation
    async def initiate_registration(
        self,
        info,
        input: UserCreateInput,
    ) -> RegistrationResponse:
        context: CustomContext = info.context
        
        if not context.redis_client:
            raise ValueError("Redis client not initialized")

        registration_service = UserRegistrationServiceUseCase(
            user_repository=SQLAlchemyUserRepository(context.session),
            otp_repository=SQLAlchemyOTPRepository(context.session),
            email_service=EmailServiceUseCase(),
            redis_client=context.redis_client
        )
        
        result = await registration_service.initiate_registration(
            email=input.email,
            password=input.password,
            is_superuser=input.is_superuser
        )
        
        return RegistrationResponse(message=result["message"])

    @strawberry.mutation
    async def verify_registration(
        self,
        info,
        email: str,
        otp: str,
    ) -> User:
        context: CustomContext = info.context
        
        if not context.redis_client:
            raise ValueError("Redis client not initialized")

        registration_service = UserRegistrationServiceUseCase(
            user_repository=SQLAlchemyUserRepository(context.session),
            otp_repository=SQLAlchemyOTPRepository(context.session),
            email_service=EmailServiceUseCase(),
            redis_client=context.redis_client
        )
        
        user, access_token = await registration_service.verify_otp(email, otp)
        
        # Set access token in cookie
        context.request.cookies["access_token"] = access_token
        
        return User(
            id=user.id,
            email=str(user.email),
            is_active=user.is_active,
            is_superuser=user.is_superuser
        )

    @strawberry.mutation
    async def resend_otp(
        self,
        info,
        email: str,
    ) -> RegistrationResponse:
        context: CustomContext = info.context
        
        if not context.redis_client:
            raise ValueError("Redis client not initialized")

        registration_service = UserRegistrationServiceUseCase(
            user_repository=SQLAlchemyUserRepository(context.session),
            otp_repository=SQLAlchemyOTPRepository(context.session),
            email_service=EmailServiceUseCase(),
            redis_client=context.redis_client
        )
        
        result = await registration_service.resend_otp(email)
        return RegistrationResponse(message=result["message"])

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation
)

async def get_context(request: Request) -> CustomContext:
    context = CustomContext(request)
    await context.__aenter__()  
    print(f"Context created in get_context: {context}, session: {context.session}")
    return context


graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context,
    graphiql=True
)