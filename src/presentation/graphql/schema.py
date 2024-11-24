from typing import List, Optional, Any
from contextlib import asynccontextmanager
from redis import Redis
import strawberry
from strawberry.fastapi import BaseContext, GraphQLRouter
from fastapi import Request, Response
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from src.infrastructure.database.connection import async_session
from src.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from src.infrastructure.repositories.otp_repository import SQLAlchemyOTPRepository
from src.application.usecases.IEmailUseCase import EmailServiceUseCase
from src.core.config import settings
from src.application.usecases.IUserRegister import UserRegistrationServiceUseCase
from src.infrastructure.config.reddis_config import RedisConfig

@strawberry.type
class RegistrationStatus:
    status: str
    message: str
    email: Optional[str] = None
    created_at: Optional[str] = None
    attempts_remaining: Optional[int] = None
    expires_in: Optional[int] = None

@strawberry.type
class RegistrationResponse:
    message: str
    status: RegistrationStatus

@strawberry.type
class User:
    id: int
    email: str
    is_active: bool
    is_superuser: bool

@strawberry.type
class VerificationResponse:
    user: User
    access_token: str

@strawberry.input
class UserCreateInput:
    email: str
    password: str
    is_superuser: Optional[bool] = False

class CustomContext(BaseContext):
    def __init__(self, request: Request):
        super().__init__()
        self.request: Request = request
        self.session: Optional[AsyncSession] = None
        self.redis_client: Optional[Redis] = None
        self.response: Response = Response()
        
    async def __aenter__(self):
        self.session = async_session()
        await self.session.__aenter__()
        redis_config = RedisConfig()
        self.redis_client = redis_config.get_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.__aexit__(exc_type, exc_val, exc_tb)
        if self.redis_client:
            self.redis_client.close()

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
    async def registration_status(
        self,
        info,
        email: str,
    ) -> RegistrationStatus:
        context: CustomContext = info.context
        
        if not context.redis_client:
            raise ValueError("Redis client not initialized")

        registration_service = UserRegistrationServiceUseCase(
            user_repository=SQLAlchemyUserRepository(context.session),
            otp_repository=SQLAlchemyOTPRepository(context.session),
            email_service=EmailServiceUseCase(),
            redis_client=context.redis_client
        )
        
        status = await registration_service.get_registration_status(email)
        return RegistrationStatus(
            status=status["status"],
            message=status["message"],
            email=status.get("email"),
            created_at=status.get("created_at"),
            attempts_remaining=status.get("attempts_remaining"),
            expires_in=status.get("expires_in")
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
        
        try:
            result = await registration_service.initiate_registration(
                email=input.email,
                password=input.password,
                is_superuser=input.is_superuser
            )
            
            return RegistrationResponse(
                message=result["message"],
                status=RegistrationStatus(
                    status=result["status"]["status"],
                    message=result["status"]["message"],
                    email=result["status"].get("email"),
                    created_at=result["status"].get("created_at"),
                    attempts_remaining=result["status"].get("attempts_remaining"),
                    expires_in=result["status"].get("expires_in")
                )
            )
        except ValueError as e:
            return RegistrationResponse(
                message=str(e),
                status=RegistrationStatus(
                    status="error",
                    message=str(e)
                )
            )

    @strawberry.mutation
    async def verify_registration(
        self,
        info,
        email: str,
        otp: str,
    ) -> VerificationResponse:
        context: CustomContext = info.context
        
        if not context.redis_client:
            raise ValueError("Redis client not initialized")

        registration_service = UserRegistrationServiceUseCase(
            user_repository=SQLAlchemyUserRepository(context.session),
            otp_repository=SQLAlchemyOTPRepository(context.session),
            email_service=EmailServiceUseCase(),
            redis_client=context.redis_client
        )
        
        try:
            user, access_token = await registration_service.verify_otp(email, otp)
            
            # Set the token in cookies
            context.response.set_cookie(
                key="access_token",
                value=f"Bearer {access_token}",
                httponly=True,
                max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert minutes to seconds
                path="/"
            )
            
            # Set the response in the context
            info.context.response = context.response
            
            return VerificationResponse(
                user=User(
                    id=user.id,
                    email=str(user.email),
                    is_active=user.is_active,
                    is_superuser=user.is_superuser
                ),
                access_token=access_token
            )
        except ValueError as e:
            raise ValueError(str(e))

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
        
        try:
            result = await registration_service.resend_otp(email)
            return RegistrationResponse(
                message=result["message"],
                status=RegistrationStatus(
                    status=result["status"]["status"],
                    message=result["status"]["message"],
                    email=result["status"].get("email"),
                    created_at=result["status"].get("created_at"),
                    attempts_remaining=result["status"].get("attempts_remaining"),
                    expires_in=result["status"].get("expires_in")
                )
            )
        except ValueError as e:
            return RegistrationResponse(
                message=str(e),
                status=RegistrationStatus(
                    status="error",
                    message=str(e)
                )
            )

schema = strawberry.Schema(query=Query, mutation=Mutation)

async def get_context(request: Request) -> CustomContext:
    context = CustomContext(request)
    await context.__aenter__()
    return context

async def get_context_with_response(request: Request, response: Response) -> CustomContext:
    context = CustomContext(request)
    context.response = response
    await context.__aenter__()
    return context

graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context_with_response,
    graphiql=True
)