from fastapi import HTTPException, status

class OceanGuardException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)

class EntityNotFoundException(OceanGuardException):
    def __init__(self, entity_name: str, identifier: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_name} with identifier '{identifier}' was not found."
        )

class ModelInferenceException(OceanGuardException):
    def __init__(self, component: str, message: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error in {component}: {message}"
        )

class InsufficientPermissionsException(OceanGuardException):
    def __init__(self, required_role: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Operation requires '{required_role}' privileges."
        )

class InvalidCredentialsException(OceanGuardException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password credentials."
        )
