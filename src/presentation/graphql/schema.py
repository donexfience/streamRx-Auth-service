from typing import List, Optional, Any
from contextlib import asynccontextmanager
from fastapi import Response,Request
from redis import Redis
import strawberry
from strawberry.fastapi import BaseContext, GraphQLRouter
from fastapi import Request, Response, Depends
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from src.infrastructure.database.connection import async_session
from src.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from src.infrastructure.repositories.otp_repository import SQLAlchemyOTPRepository
from src.application.usecases.IEmailUseCase import EmailServiceUseCase
from src.core.config import settings
from src.application.usecases.IUserRegister import UserRegistrationServiceUseCase
from src.infrastructure.config.reddis_config import RedisConfig
from src.__lib.UserRole import UserRole
from src.application.usecases.IloginUseCase import LoginUseCase
from typing import Dict
import logging
from src.infrastructure.repositories.forgetPasswordTokenRepository import ForgotPasswordTokenRepository
from src.application.usecases.IForgetPasswordUsecase import ForgotPasswordUseCase
from src.application.usecases.IChangePasswordUsecase import ChangePasswordUseCase
from src.application.services.password_service import PasswordServiceUseCase
from src.application.usecases.IGoogleLoginUsecase import GoogleLoginUseCase
from src.application.usecases.ItokenUseCases import TokenServiceUseCase
from datetime import datetime

# Setting up logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class RegistrationError(Exception):
    pass

# Context manager for session and Redis client
@asynccontextmanager
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

@asynccontextmanager
async def get_redis_client() -> Redis:
    redis_config = RedisConfig()
    redis_client = redis_config.get_client()
    yield redis_client
    redis_client.close()

@strawberry.type
class ForgotPasswordResponse:
    message: str
    success: bool
    reset_link: Optional[str] = None

@strawberry.input
class ChangePasswordInput:
    token: str
    new_password: str



@strawberry.input
class ResetPasswordInput:
    token: str
    new_password: str



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
    is_verified: bool
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    role: str
    name:Optional[str]=None

@strawberry.type
class Token:
    access_token :str
    refresh_token :str

@strawberry.input
class GoogleLoginInput:
    email: str
    google_id: Optional[str]
    name: Optional[str]

@strawberry.type
class VerificationResponse:
    user: User
    token: Optional[Token] 



@strawberry.input
class UserCreateInput:
    email: str
    password: str
    bio: Optional[str] = "write something"
    username: Optional[str] = None
    profile_image_url: Optional[str] = "https://example.com/profile.jpg"
    date_of_birth: Optional[str] = None
    phone_number: Optional[str] = None
    
@strawberry.input
class LoginInput:
    email:str
    password:str

@strawberry.type
class LoginResponse:
    success:bool
    message:str
    user: Optional["User"]  
    token: Optional[Token] 

class CustomContext(BaseContext):
    def __init__(self, request: Request):
        super().__init__()
        self.request: Request = request
        self.session: Optional[AsyncSession] = None
        self.redis_client: Optional[Redis] = None
        self.response: Response = request.scope.get('response') 

    async def __aenter__(self):
        async with get_session() as session:
            self.session = session
            async with get_redis_client() as redis_client:
                self.redis_client = redis_client
                return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.session = None
        self.redis_client = None

@strawberry.type
class Query:
    @strawberry.field
    async def users(self, info, skip: int = 0, limit: int = 100) -> List[User]:
        context: CustomContext = info.context
        async with get_session() as session:
            repository = SQLAlchemyUserRepository(session)
            users = await repository.list_users(skip=skip, limit=limit)
            return [
                User(
                    id=user.id,
                    email=str(user.email),
                    is_active=user.is_active,
                    bio=user.bio,
                    profile_image_url=user.profileImageURL,
                    role=user.role.value,
                )
                for user in users
            ]

    @strawberry.field
    async def registration_status(self, info, email: str) -> RegistrationStatus:
        context: CustomContext = info.context
        async with get_redis_client() as redis_client:
            registration_service = UserRegistrationServiceUseCase(
                user_repository=SQLAlchemyUserRepository(context.session),
                otp_repository=SQLAlchemyOTPRepository(context.session),
                email_service=EmailServiceUseCase(),
                redis_client=redis_client,
            )
            status = await registration_service.get_registration_status(email)
            print(status,"status of seession")
            return RegistrationStatus(
                status=status["status"],
                message=status["message"],
                email=status.get("email"),
                created_at=status.get("created_at"),
                attempts_remaining=status.get("attempts_remaining"),
                expires_in=status.get("expires_in"),
            )

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def initiate_registration(self, info, input: UserCreateInput) -> RegistrationResponse:
        bio = input.bio or None
        username = input.username or None
        profile_image_url = input.profile_image_url or None
        date_of_birth = input.date_of_birth or None
        phone_number = input.phone_number or None
        context: CustomContext = info.context
        try:
            print(input.phone_number,input.date_of_birth,input.username)
            async with get_redis_client() as redis_client, get_session() as session:
                registration_service = UserRegistrationServiceUseCase(
                    user_repository=SQLAlchemyUserRepository(session),
                    otp_repository=SQLAlchemyOTPRepository(session),
                    email_service=EmailServiceUseCase(),
                    redis_client=redis_client,
                )

                logger.info(f"Initiating registration for {input.email}")

                result = await registration_service.initiate_registration(
                    email=input.email,
                    password=input.password,
                    role=UserRole.VIEWER,
                    is_active=True,
                    bio=bio,
                    profile_image_url=profile_image_url,
                    date_of_birth=date_of_birth,
                    phone_number=phone_number,
                    username=username
                )

                logger.info(f"Registration result: {result}")

                return RegistrationResponse(
                    message=result["message"],
                    status=RegistrationStatus(
                        status=result["status"]["status"],
                        message=result["status"]["message"],
                        email=result["status"].get("email"),
                        created_at=result["status"].get("created_at"),
                        attempts_remaining=result["status"].get("attempts_remaining"),
                        expires_in=result["status"].get("expires_in"),
                    ),
                )
        except RegistrationError as e:
            logger.error(f"Registration error for {input.email}: {str(e)}")
            return RegistrationResponse(
                message=str(e),
                status=RegistrationStatus(
                    status="error",
                    message=str(e),
                ),
            )

    @strawberry.mutation
    async def verify_registration(self, info, email: str, otp: str) -> VerificationResponse:
        context: CustomContext = info.context

        try:
            async with get_redis_client() as redis_client, get_session() as session:
                registration_service = UserRegistrationServiceUseCase(
                    user_repository=SQLAlchemyUserRepository(session),
                    otp_repository=SQLAlchemyOTPRepository(session),
                    email_service=EmailServiceUseCase(),
                    redis_client=redis_client,
                )

                logger.info(f"Verifying OTP for {email}")

                user, access_token ,refresh_token = await registration_service.verify_otp(email, otp)
                print(refresh_token,"token-refresh")

                logger.info(f"OTP verified for {email}, issuing access token")

                # Set the token in cookies
                context.response.set_cookie(
                    key="access_token",
                    value=f"Bearer {access_token}",
                    httponly=True,
                    max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert minutes to seconds
                )

                context.response.set_cookie(
                    key="refresh_token",
                    value=f"Bearer {refresh_token}",
                    httponly=True,
                    max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # Days to seconds
                )   
                
                info.context.response = context.response
                tokens = Token(access_token=access_token,refresh_token=refresh_token)
                print(f"accesstoken{access_token},refreshtoken{refresh_token}")
                return VerificationResponse(
                    user=User(
                        id=user.id,
                        email=str(user.email),
                        is_active=user.is_active,
                        bio=user.bio,
                        profile_image_url=user.profileImageURL,
                        role=user.role.value,
                        is_verified=user.is_verified,
                    ),
                    token=tokens
                )
            
        except RegistrationError as e:
            logger.error(f"OTP verification failed for {email}: {str(e)}")
            raise RegistrationError(f"OTP verification failed: {str(e)}")

    @strawberry.mutation
    async def resend_otp(self, info, email: str) -> RegistrationResponse:
        context: CustomContext = info.context

        try:
            async with get_redis_client() as redis_client, get_session() as session:
                registration_service = UserRegistrationServiceUseCase(
                    user_repository=SQLAlchemyUserRepository(session),
                    otp_repository=SQLAlchemyOTPRepository(session),
                    email_service=EmailServiceUseCase(),
                    redis_client=redis_client,
                )

                logger.info(f"Resending OTP to {email}")

                result = await registration_service.resend_otp(email)

                return RegistrationResponse(
                    message=result["message"],
                    status=RegistrationStatus(
                        status=result["status"]["status"],
                        message=result["status"]["message"],
                        email=result["status"].get("email"),
                        created_at=result["status"].get("created_at"),
                        attempts_remaining=result["status"].get("attempts_remaining"),
                        expires_in=result["status"].get("expires_in"),
                    ),
                )
        except RegistrationError as e:
            logger.error(f"Resending OTP failed for {email}: {str(e)}")
            return RegistrationResponse(
                message=str(e),
                status=RegistrationStatus(
                    status="error",
                    message=str(e),
                ),
            )  
        
    @strawberry.mutation    
    async def login(self, info, input: LoginInput) -> LoginResponse:
        context: CustomContext = info.context
        async with get_redis_client() as redis_client, get_session() as session:
            user_repository = SQLAlchemyUserRepository(session)
            login_use_case = LoginUseCase(user_repository=user_repository)
        
            result = await login_use_case.Login(input.email, input.password)
            print(result["success"],result["message"],"loginnnnnnnnnnnnn result")
        
            if not result["success"]:
                return LoginResponse(
                success=False,
                message=result["message"],
                user=None,
                token=None, 
                )
        
        user_data = result["user"]
        tokens = result["tokens"]
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
    
        context.response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        context.response.set_cookie(
            key="refresh_token",
            value=f"Bearer {refresh_token}",
            httponly=True,
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )
    
        tokens = Token(access_token=access_token, refresh_token=refresh_token)
        return LoginResponse(
            success=True,
            message="Login successful",
            user=User(
                id=user_data["id"],
                email=user_data["email"],
                role=user_data["role"],
                is_verified=user_data["is_verified"],
                is_active=user_data["is_active"] 
            ),
            token=tokens 
        )
    @strawberry.mutation
    async def loginStreamer(self, info, input: LoginInput) -> LoginResponse:
        context: CustomContext = info.context
        async with get_redis_client() as redis_client, get_session() as session:
            user_repository = SQLAlchemyUserRepository(session)
            login_use_case = LoginUseCase(user_repository=user_repository)
        
            result = await login_use_case.StreamerLogin(input.email, input.password)
            print(result["success"],result["message"],"loginnnnnnnnnnnnn result")
        
            if not result["success"]:
                return LoginResponse(
                success=False,
                message=result["message"],
                user=None,
                token=None, 
                )
        
        user_data = result["user"]
        tokens = result["tokens"]
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
    
        context.response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        context.response.set_cookie(
            key="refresh_token",
            value=f"Bearer {refresh_token}",
            httponly=True,
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )
    
        tokens = Token(access_token=access_token, refresh_token=refresh_token)
        return LoginResponse(
            success=True,
            message="Login successful",
            user=User(
                id=user_data["id"],
                email=user_data["email"],
                role=user_data["role"],
                is_verified=user_data["is_verified"],
                is_active=user_data["is_active"] 
            ),
            token=tokens 
        )   
    @strawberry.mutation
    async def forgot_password(self, email: str, info) -> ForgotPasswordResponse:
        context: CustomContext = info.context
        async with get_session() as session:
            token_repository = ForgotPasswordTokenRepository(session)
            email_service = EmailServiceUseCase()
            user_repository = SQLAlchemyUserRepository(session)
            user = await user_repository.get_by_email(email)
            if not user:
                return ForgotPasswordResponse(
                success=False,
                message="User not found"
                )
        
            try:
            
                forgot_password_use_case = ForgotPasswordUseCase(
                token_repository=token_repository,
                email_service=email_service,
                )
                print("working try ")
                print("user ",user)
                # Generate the reset link and send email
                reset_link = await forgot_password_use_case.request_password_reset(user_id=user.id, email=email)
                print(reset_link,"reset link")
                return ForgotPasswordResponse(
                success=True,
                message="Reset link sent to your email",
                reset_link=reset_link 
                )
            except Exception as e:
                return ForgotPasswordResponse(
                    success=False,
                    message=str(e)
                )
    @strawberry.mutation
    async def change_password(self, info, input: ChangePasswordInput) -> ForgotPasswordResponse:
        context: CustomContext = info.context
        async with get_session() as session:
            try:
                print('hello from change password')
                user_repository = SQLAlchemyUserRepository(session)
                forgot_token_repository = ForgotPasswordTokenRepository(session)
                password_service = PasswordServiceUseCase
                change_password_use_case = ChangePasswordUseCase(user_repository, password_service, forgot_token_repository)
                token_record = await forgot_token_repository.get_token(input.token)
                print(token_record,input.token,"token used")
                if not token_record:
                    raise ValueError("Invalid or expired token")
                message = await change_password_use_case.execute(token_record.user_id, token_record, input.new_password)
                print(message,"message aftere change")
                return ForgotPasswordResponse(
                    success=True,
                    message=message
                )
            except ValueError as e:
                return ForgotPasswordResponse(
                    success=False,
                    message=f"Error: {str(e)}"
                )
            except Exception as e:
                # Catch unexpected errors
                return ForgotPasswordResponse(
                    success=False,
                    message=f"An unexpected error occurred: {str(e)}"
                )    
    @strawberry.mutation
    async def Logout(self, info) -> bool:
        context: CustomContext = info.context
        response: Response = context.response  
        try:
            
            response.delete_cookie(key="access_token")
            response.delete_cookie(key="refresh_token")
            return True
        except Exception as e:
            print(f"Error during logout: {e}")
            return False
    
    @strawberry.mutation
    async def google_login(self, info, input: GoogleLoginInput) -> LoginResponse:
        context: CustomContext = info.context
        try:
            async with get_session() as session:

                user_repository = SQLAlchemyUserRepository(session)
                login_use_case = GoogleLoginUseCase(user_repository=user_repository,token_service=TokenServiceUseCase)

                # Perform Google login logic
                result = await login_use_case.execute(
                    email=input.email,
                    google_id=input.google_id,
                    name=input.name
                )
                access_token = result['tokens']['access_token']
                refresh_token = result['tokens']['refresh_token']
                context.response.set_cookie(
                    key="access_token",
                    value=f"Bearer {access_token}",
                    httponly=True,
                    max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  
                )
                context.response.set_cookie(
                    key="refresh_token",
                    value=f"Bearer {refresh_token}",
                    httponly=True,
                    max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  
                )
                return LoginResponse(
                    success=True,
                    message="Google login successful",
                    user=User(
                        id=result['user']['id'],
                        email=result['user']['email'],
                        role=result['user']['role'],
                        is_verified=result['user']['is_verified'],
                        is_active=result['user']['is_active']
                    ),
                    token=Token(
                        access_token=access_token,
                        refresh_token=refresh_token
                    )
                )
        except Exception as e:
            logger.error(f"Error during Google login: {str(e)}")
            return LoginResponse(
                success=False,
                message=f"Google login failed: {str(e)}",
                user=None,
                token=None
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

graphql_app = GraphQLRouter(schema, context_getter=get_context_with_response)
