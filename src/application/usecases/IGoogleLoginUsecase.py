from typing import Optional, Dict
from src.domain.entities.user import User, UserRole


class GoogleLoginUseCase:
    def __init__(self, user_repository, token_service,grpc_client):
        self.user_repository = user_repository
        self.token_service = token_service
        self.grpc_client = grpc_client

    async def execute(self, email: str, name: Optional[str] = None, google_id: Optional[str] = None) -> Dict:
        try:
            user: Optional[User] = await self.user_repository.get_by_email(email)
            if not user:
                user = await self.user_repository.create(
                    User(
                        email=email,
                        role=UserRole.VIEWER,
                        bio=None,
                        is_verified=True,
                        is_active=True,
                        google_id=google_id
                    )
                )
                print("user searched with google deatilas",user)
                await self.grpc_client.send_user_data(user)
            elif not user.google_id and google_id:
                print("no goolge id")
                user = await self.user_repository.updateWithGoogle(user.id, google_id=google_id)
                await self.grpc_client.send_user_data(user)
            tokens = {
                "access_token": self.token_service.create_access_token({
                    "user_id": user.id,
                    "role": user.role.value  
                }),
                "refresh_token": self.token_service.create_refresh_token({
                    "user_id": user.id,
                    "role": user.role.value 
                })
            }
            response_data = {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role.value, 
                    "is_verified": user.is_verified,
                    "is_active": user.is_active,
                },
                "tokens": tokens
            }

            return response_data

        except Exception as e:
            error_message = f"Error during Google login in use case google: {e}"
            print(error_message)
            raise RuntimeError(error_message) from e
