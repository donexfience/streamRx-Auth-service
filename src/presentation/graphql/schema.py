from typing import List, Optional, Any
from contextlib import asynccontextmanager
import strawberry
from strawberry.fastapi import BaseContext, GraphQLRouter
from fastapi import Request
from sqlalchemy.ext.asyncio import async_sessionmaker,AsyncSession
from src.infrastructure.database.connection import async_session
from src.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from src.application.use_cases.user.create_user import CreateUserUseCase, CreateUserInput

class CustomContext(BaseContext):
    def __init__(self, request: Request):
        super().__init__()
        self.request: Request = request
        self.session: Optional[AsyncSession] = None

    async def __aenter__(self):
        # Initialize the session
        self.session = async_session()  # Ensure async_session is defined
        print(f"Session initialized in __aenter__: {self.session}")
        await self.session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Clean up the session
        print("Closing session in __aexit__")
        if self.session:
            await self.session.__aexit__(exc_type, exc_val, exc_tb)

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
    async def create_user(
        self,
        info,
        input: UserCreateInput,
    ) -> User:
        context: CustomContext = info.context
        print("context got in the creation mutation",context,context.session)
        repository = SQLAlchemyUserRepository(context.session)
        use_case = CreateUserUseCase(repository)
        if repository is None:
            raise ValueError("Repository not initialized properly.")
        else:
            print('repostiory got')
        use_case = CreateUserUseCase(repository)
        
        # Ensure use_case is initialized
        if use_case is None:
            raise ValueError("CreateUserUseCase not initialized properly.")
        else:
            print("user case is got")
        print(input.email,input.password,input.is_superuser,"data is coming from the server and getting in the mutation")
        user = await use_case.execute(CreateUserInput(
            email=input.email,
            password=input.password,
            is_superuser=input.is_superuser
        ))
        print(user,"user created in the schema")
        return User(
            id=user.id,
            email=str(user.email),
            is_active=user.is_active,
            is_superuser=user.is_superuser
        )
        
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