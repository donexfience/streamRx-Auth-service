from fastapi import HTTPException, status

class CustomHTTPException(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)

class NotFoundException(CustomHTTPException):
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)

class UnauthorizedException(CustomHTTPException):
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)

class ForbiddenException(CustomHTTPException):
    def __init__(self, detail: str = "Not enough privileges"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)

class ValidationException(CustomHTTPException):
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)