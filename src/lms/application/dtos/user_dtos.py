"""User-related DTOs.

Data Transfer Objects (DTOs) provide a clean boundary between the API layer
and the domain layer. They serve several purposes:

1. Input Validation: Using Pydantic ensures request data is validated before
   reaching the domain layer, maintaining domain integrity.

2. API Contract Stability: DTOs allow the domain model to evolve independently
   of API contracts, providing backward compatibility.

3. Security: DTOs prevent exposing internal domain details and allow us to
   control exactly what data is exposed to clients.
"""

from pydantic import BaseModel, Field, EmailStr
from uuid import UUID


class CreateUserRequest(BaseModel):
    """Request to create a user.

    This DTO validates incoming user creation requests at the API boundary.
    Using Pydantic provides automatic validation, serialization, and clear
    error messages for invalid data.
    """

    email: EmailStr
    name: str = Field(..., min_length=1)
    role: str = Field(..., pattern=r"^(student|tutor)$")


class UserResponse(BaseModel):
    """User response.

    This DTO represents user data returned to clients. It's a simplified
    representation that excludes internal domain details like value objects.

    Note: We return email as a plain string (not EmailStr) because it's
    already validated in the domain and we want to avoid re-validation overhead.
    """

    id: UUID
    email: str
    name: str
    role: str
