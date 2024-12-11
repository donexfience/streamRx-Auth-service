import grpc
from src.generated import user_pb2, user_pb2_grpc
import os

class UserServiceClient:
    def __init__(self, address=None):
        address = os.getenv('USER_SERVICE_URL', 'localhost:50051')
        try:
            self.channel = grpc.aio.insecure_channel(address)
            self.stub = user_pb2_grpc.UserServiceStub(self.channel)
            print(f"Successfully created gRPC channel to {address}")
        except Exception as e:
            print(f"Error creating gRPC channel: {e}")

    async def send_user_data(self, user_data):
        print(user_data, "user data in the grpc")
        
        try:
            # Handle role conversion
            role = (str(user_data.role.name) if hasattr(user_data, 'role') 
                    and user_data.role is not None else 'VIEWER')
            print(user_data,"user data got")
            # Detailed field conversion with explicit handling of None values
            user = user_pb2.User(
                id=str(user_data.id) if user_data.id is not None else '',
                email=str(user_data.email) if user_data.email is not None else '',
                hashed_password=str(user_data.hashed_password) if hasattr(user_data, 'hashed_password') else '',
                role=role,
                bio=str(user_data.bio) if user_data.bio is not None else '',
                is_verified=bool(user_data.is_verified) if hasattr(user_data, 'is_verified') else True,
                profile_image_url=str(user_data.profileImageURL) if user_data.profileImageURL is not None else '',
                is_active=bool(user_data.is_active) if hasattr(user_data, 'is_active') else True,
                phone_number=str(user_data.phone_number) if user_data.phone_number is not None else '',
                date_of_birth=str(user_data.date_of_birth) if user_data.date_of_birth is not None else '',
                username=str(user_data.username) if user_data.username is not None else ''
            )
            
            # Detailed logging of the converted user object
            print("Converted gRPC User Object:")
            print(f"ID: {user.id}")
            print(f"Email: {user.email}")
            print(f"Role: {user.role}")
            print(f"Hashed Password: {user.hashed_password[:10]}...")  # Partial password for security
            print(f"Is Verified: {user.is_verified}")
            print(f"Is Active: {user.is_active}")
            print(f"Profile Image URL: {user.profile_image_url}")
            print(f"Username: {user.username}")
            print(f"Phone Number: {user.phone_number}")
            print(f"Date of Birth: {user.date_of_birth}")
            print(f"Bio: {user.bio}")
            
            request = user_pb2.CreateUserRequest(user=user)
            response = await self.stub.CreateUser(request)

            return {
                "success": response.success,
                "message": response.message
            }

        except Exception as error:
            print(f"Detailed Error: {error}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"An error occurred: {error}"
            }